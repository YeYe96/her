"""
记忆管理模块 - Amadeus 三层记忆系统

Layer 1: 工作记忆 (Working Memory) - 最近 20 轮原始对话
Layer 2: 情景记忆 (Episodic Memory) - 重要事件摘要 (ChromaDB)
Layer 3: 语义记忆 (Semantic Memory) - 用户画像/偏好
"""

import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from uuid import uuid4

# ChromaDB 导入 (如果可用)
try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    print("[Memory] ChromaDB not installed. Long-term memory disabled.")


class MemoryManager:
    """
    Amadeus 记忆管理器
    
    管理三层记忆系统：
    1. 工作记忆：最近 N 轮对话，直接注入 LLM
    2. 情景记忆：压缩后的历史对话，支持 RAG 检索
    3. 语义记忆：用户画像，持久化到文件
    """
    
    MAX_WORKING_MEMORY_TURNS = 20  # 保留最近 20 轮 (40 条消息)
    EVICTION_BUFFER_SIZE = 50      # 缓冲区大小：累积 50 轮后批量提取
    
    def __init__(self, data_dir: str = None):
        """
        初始化记忆管理器
        
        Args:
            data_dir: 数据存储目录，默认为 server/data
        """
        # 数据目录
        if data_dir is None:
            self.data_dir = Path(__file__).parent.parent / "data"
        else:
            self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Layer 1: 工作记忆 (内存) - 即时上下文
        self.working_memory: List[Dict[str, str]] = []
        
        # Layer 2: 驱逐缓冲区 (内存) - 待批量处理
        self.eviction_buffer: List[Dict[str, str]] = []
        self.buffer_path = self.data_dir / "eviction_buffer.json"
        self._load_buffer()  # 恢复未处理的缓冲区
        
        # Layer 3: 语义记忆 / 用户画像
        self.profile_path = self.data_dir / "user_profile.json"
        self.user_profile = self._load_profile()
        
        # Ollama 配置 (用于批量提取)
        from config.settings import settings
        self.ollama_url = settings.OLLAMA_HOST
        self.ollama_model = settings.MODEL_NAME
        
        # Layer 2 备用: ChromaDB (如果可用)
        self.chroma_client = None
        self.episodic_collection = None
        if CHROMA_AVAILABLE:
            self._init_chromadb()
        
        print(f"[Memory] Initialized. Data dir: {self.data_dir}")
        print(f"[Memory] Working memory: {self.MAX_WORKING_MEMORY_TURNS} turns")
        print(f"[Memory] Eviction buffer: {len(self.eviction_buffer)}/{self.EVICTION_BUFFER_SIZE}")
        print(f"[Memory] ChromaDB: {'Enabled' if CHROMA_AVAILABLE else 'Disabled'}")
    
    # ==================== Layer 1: 工作记忆 ====================
    
    def add_turn(self, user_msg: str, assistant_msg: str) -> None:
        """
        添加一轮对话到工作记忆
        
        Args:
            user_msg: 用户消息
            assistant_msg: AI 回复
        """
        self.working_memory.append({"role": "user", "content": user_msg})
        self.working_memory.append({"role": "assistant", "content": assistant_msg})
        
        # 检查是否需要压缩
        self._trim_working_memory()
    
    def get_context_messages(self) -> List[Dict[str, str]]:
        """
        获取工作记忆中的所有消息，用于注入 LLM 上下文
        
        Returns:
            消息列表，格式: [{"role": "user/assistant", "content": "..."}]
        """
        return self.working_memory.copy()
    
    def _trim_working_memory(self) -> None:
        """
        当工作记忆超过限制时，移除最早的对话并放入缓冲区
        当缓冲区满时，触发批量信息提取
        """
        max_messages = self.MAX_WORKING_MEMORY_TURNS * 2  # 每轮 2 条消息
        
        while len(self.working_memory) > max_messages:
            # 移除最早的一轮 (2 条消息)
            removed_user = self.working_memory.pop(0)
            removed_assistant = self.working_memory.pop(0)
            
            # 放入驱逐缓冲区
            self.eviction_buffer.append({
                "user": removed_user["content"],
                "assistant": removed_assistant["content"],
                "timestamp": datetime.now().isoformat()
            })
            self._save_buffer()
            
            print(f"[Memory] Evicted to buffer: {len(self.eviction_buffer)}/{self.EVICTION_BUFFER_SIZE}")
            
            # 缓冲区满时，触发批量提取
            if len(self.eviction_buffer) >= self.EVICTION_BUFFER_SIZE:
                asyncio.create_task(self._batch_extract_user_info())
    
    def clear_working_memory(self) -> None:
        """清空工作记忆"""
        self.working_memory.clear()
        print("[Memory] Working memory cleared.")
    
    # ==================== Layer 2: 驱逐缓冲区 ====================
    
    def _load_buffer(self) -> None:
        """加载未处理的缓冲区"""
        if self.buffer_path.exists():
            try:
                with open(self.buffer_path, 'r', encoding='utf-8') as f:
                    self.eviction_buffer = json.load(f)
                    if self.eviction_buffer:
                        print(f"[Memory] Restored {len(self.eviction_buffer)} buffered conversations")
            except Exception as e:
                print(f"[Memory] Failed to load buffer: {e}")
                self.eviction_buffer = []
    
    def _save_buffer(self) -> None:
        """保存缓冲区到文件 (断电恢复)"""
        try:
            with open(self.buffer_path, 'w', encoding='utf-8') as f:
                json.dump(self.eviction_buffer, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Memory] Failed to save buffer: {e}")
    
    async def _batch_extract_user_info(self) -> None:
        """
        批量提取用户信息：当缓冲区满时调用 LLM 提取关键信息
        """
        import httpx
        
        if not self.eviction_buffer:
            return
        
        print(f"[Memory] 🔄 Batch extracting from {len(self.eviction_buffer)} conversations...")
        
        try:
            # 构建对话内容
            conversations = []
            for turn in self.eviction_buffer:
                conversations.append(f"用户: {turn['user']}")
                conversations.append(f"红莉栖: {turn['assistant']}")
            
            conversations_text = "\n".join(conversations)
            
            # 使用外部提示词模板
            from core.prompts import EXTRACTION_PROMPT
            prompt = EXTRACTION_PROMPT.format(conversations=conversations_text)
            
            # 调用 Ollama
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_url}/api/chat",
                    json={
                        "model": self.ollama_model,
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False,
                        "options": {"num_predict": 500}
                    },
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result.get("message", {}).get("content", "")
                    
                    # 尝试解析 JSON
                    extracted = self._parse_extraction_result(content)
                    
                    if extracted:
                        self._merge_extracted_info(extracted)
                        print(f"[Memory] ✅ Extracted info: {extracted}")
                    
                    # 清空缓冲区
                    self.eviction_buffer.clear()
                    self._save_buffer()
                    print("[Memory] Buffer cleared after extraction")
                    
        except Exception as e:
            print(f"[Memory] ❌ Batch extraction failed: {e}")
            # 失败时不清空缓冲区，下次重试
    
    def _parse_extraction_result(self, content: str) -> Optional[Dict[str, Any]]:
        """解析 LLM 返回的 JSON 结果"""
        try:
            # 尝试提取 JSON 部分
            import re
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            print(f"[Memory] JSON parse failed: {e}")
        return None
    
    def _merge_extracted_info(self, extracted: Dict[str, Any]) -> None:
        """将提取的信息合并到用户画像"""
        updated = False
        
        # 合并名字
        if extracted.get("name") and not self.user_profile.get("name"):
            self.user_profile["name"] = extracted["name"]
            updated = True
        
        # 合并兴趣
        for interest in extracted.get("interests", []):
            if interest and interest not in self.user_profile["interests"]:
                self.user_profile["interests"].append(interest)
                updated = True
        
        # 合并事实
        for fact in extracted.get("facts", []):
            if fact and fact not in self.user_profile["important_facts"]:
                self.user_profile["important_facts"].append(fact)
                updated = True
        
        # 合并偏好
        for key, value in extracted.get("preferences", {}).items():
            if key and value:
                self.user_profile["preferences"][key] = value
                updated = True
        
        if updated:
            self._save_profile()
            print("[Memory] User profile updated with extracted info")
    
    # ==================== Layer 2: 情景记忆 (ChromaDB) ====================
    
    def _init_chromadb(self) -> None:
        """初始化 ChromaDB 客户端和集合"""
        try:
            chroma_path = self.data_dir / "chroma"
            self.chroma_client = chromadb.PersistentClient(
                path=str(chroma_path),
                settings=ChromaSettings(anonymized_telemetry=False)
            )
            self.episodic_collection = self.chroma_client.get_or_create_collection(
                name="amadeus_episodic",
                metadata={"description": "Amadeus conversation episodes"}
            )
            print(f"[Memory] ChromaDB initialized at {chroma_path}")
        except Exception as e:
            print(f"[Memory] ChromaDB init failed: {e}")
            self.chroma_client = None
            self.episodic_collection = None
    
    async def _archive_to_episodic(
        self, 
        user_msg: Dict[str, str], 
        assistant_msg: Dict[str, str]
    ) -> None:
        """
        将一轮对话归档到情景记忆
        
        Args:
            user_msg: 用户消息
            assistant_msg: AI 回复
        """
        if self.episodic_collection is None:
            return
        
        try:
            # 构建文档内容
            document = f"用户: {user_msg['content']}\n红莉栖: {assistant_msg['content']}"
            
            # 存入 ChromaDB
            self.episodic_collection.add(
                documents=[document],
                metadatas=[{
                    "type": "conversation",
                    "timestamp": datetime.now().isoformat(),
                    "user_preview": user_msg['content'][:100]
                }],
                ids=[str(uuid4())]
            )
            print(f"[Memory] Archived to episodic: {user_msg['content'][:50]}...")
        except Exception as e:
            print(f"[Memory] Archive failed: {e}")
    
    def search_episodic(self, query: str, top_k: int = 3) -> List[str]:
        """
        在情景记忆中搜索相关历史
        
        Args:
            query: 搜索查询
            top_k: 返回的最大结果数
            
        Returns:
            相关历史对话列表
        """
        if self.episodic_collection is None:
            return []
        
        try:
            results = self.episodic_collection.query(
                query_texts=[query],
                n_results=top_k
            )
            documents = results.get("documents", [[]])[0]
            return documents
        except Exception as e:
            print(f"[Memory] Search failed: {e}")
            return []
    
    # ==================== Layer 3: 语义记忆 (用户画像) ====================
    
    def _load_profile(self) -> Dict[str, Any]:
        """加载用户画像"""
        default_profile = {
            "name": None,
            "interests": [],
            "preferences": {},
            "important_facts": [],
            "relationship_notes": [],
            "last_updated": None
        }
        
        if self.profile_path.exists():
            try:
                with open(self.profile_path, 'r', encoding='utf-8') as f:
                    profile = json.load(f)
                    print(f"[Memory] Loaded user profile with {len(profile.get('important_facts', []))} facts")
                    return profile
            except Exception as e:
                print(f"[Memory] Failed to load profile: {e}")
        
        return default_profile
    
    def _save_profile(self) -> None:
        """保存用户画像"""
        try:
            self.user_profile["last_updated"] = datetime.now().isoformat()
            with open(self.profile_path, 'w', encoding='utf-8') as f:
                json.dump(self.user_profile, f, ensure_ascii=False, indent=2)
            print("[Memory] User profile saved.")
        except Exception as e:
            print(f"[Memory] Failed to save profile: {e}")
    
    def update_profile(self, category: str, content: str) -> None:
        """
        更新用户画像
        
        Args:
            category: 类别 (interest, preference, fact, relationship)
            content: 内容
        """
        if category == "interest" and content not in self.user_profile["interests"]:
            self.user_profile["interests"].append(content)
        elif category == "fact" and content not in self.user_profile["important_facts"]:
            self.user_profile["important_facts"].append(content)
        elif category == "relationship":
            self.user_profile["relationship_notes"].append(content)
        elif category == "name":
            self.user_profile["name"] = content
        
        self._save_profile()
    
    def get_profile_summary(self) -> str:
        """
        获取用户画像摘要，用于注入系统提示
        
        Returns:
            用户画像描述字符串
        """
        parts = []
        
        if self.user_profile.get("name"):
            parts.append(f"用户名字: {self.user_profile['name']}")
        
        if self.user_profile.get("interests"):
            interests = ", ".join(self.user_profile["interests"][:5])
            parts.append(f"用户兴趣: {interests}")
        
        if self.user_profile.get("important_facts"):
            facts = "; ".join(self.user_profile["important_facts"][:5])
            parts.append(f"已知信息: {facts}")
        
        return "\n".join(parts) if parts else ""
    
    # ==================== 统计信息 ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """获取记忆系统统计信息"""
        stats = {
            "working_memory_turns": len(self.working_memory) // 2,
            "working_memory_messages": len(self.working_memory),
            "user_profile_facts": len(self.user_profile.get("important_facts", [])),
            "user_profile_interests": len(self.user_profile.get("interests", [])),
            "chromadb_enabled": self.episodic_collection is not None
        }
        
        if self.episodic_collection:
            try:
                stats["episodic_count"] = self.episodic_collection.count()
            except:
                stats["episodic_count"] = 0
        
        return stats


# 全局单例
_memory_instance: Optional[MemoryManager] = None

def get_memory_manager() -> MemoryManager:
    """获取记忆管理器单例"""
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = MemoryManager()
    return _memory_instance
