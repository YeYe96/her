"""
AI 服务抽象层 - 符合 4.2 接口解耦规范

通过抽象基类封装 AI 调用逻辑，便于未来切换不同的 AI 后端：
- 当前: Ollama (本地)
- 未来: OpenAI, DeepSeek, 通义千问等
"""

import time
from abc import ABC, abstractmethod
from typing import Optional, Tuple
import httpx

from config.settings import settings
from core.personality import SYSTEM_PROMPT


class BaseAIService(ABC):
    """
    AI 服务抽象基类
    
    所有 AI 服务实现都必须继承此类并实现 chat 方法。
    这样上层业务逻辑不依赖具体实现，便于切换 AI 后端。
    """
    
    @abstractmethod
    async def chat(
        self, 
        text: str, 
        image_base64: Optional[str] = None
    ) -> Tuple[str, int]:
        """
        发送聊天请求
        
        Args:
            text: 用户输入的文本
            image_base64: 可选的图片 Base64 编码
            
        Returns:
            Tuple[str, int]: (AI 回复内容, 延迟毫秒数)
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        检查服务是否可用
        
        Returns:
            bool: 服务是否正常
        """
        pass


class OllamaService(BaseAIService):
    """
    Ollama 服务实现
    
    通过 Ollama REST API 调用本地运行的大语言模型。
    支持文本和多模态（图片）输入。
    集成记忆系统，支持对话上下文。
    """
    
    def __init__(self):
        self.base_url = settings.OLLAMA_HOST
        self.model = settings.MODEL_NAME
        self.timeout = settings.REQUEST_TIMEOUT
        
        # DEBUG: 显示实际使用的 Ollama 地址
        print(f"[OllamaService] Initialized with base_url: {self.base_url}")
        
        # 初始化记忆管理器
        from core.memory import get_memory_manager
        self.memory = get_memory_manager()
        
    async def chat(
        self, 
        text: str, 
        image_base64: Optional[str] = None
    ) -> Tuple[str, int]:
        """
        发送聊天请求到 Ollama
        
        Args:
            text: 用户输入的文本
            image_base64: 可选的图片 Base64 编码
            
        Returns:
            Tuple[str, int]: (AI 回复内容, 延迟毫秒数)
        """
        start_time = time.time()
        
        print("\n" + "="*60)
        print("[AI] Inference Started")
        print("="*60)
        
        # ==================== 构建增强系统提示 ====================
        # 检索相关历史记忆 (RAG)
        relevant_memories = self.memory.search_episodic(text, top_k=3)
        
        # 获取用户画像
        user_profile = self.memory.get_profile_summary()
        
        # 构建增强的系统提示
        enhanced_prompt = SYSTEM_PROMPT
        if user_profile:
            enhanced_prompt += f"\n\n## 用户信息\n{user_profile}"
        if relevant_memories:
            memories_text = "\n".join([f"- {m}" for m in relevant_memories])
            enhanced_prompt += f"\n\n## 相关记忆\n{memories_text}"
        
        # ==================== 构建消息列表 ====================
        messages = [
            {"role": "system", "content": enhanced_prompt}
        ]
        
        # 注入工作记忆 (最近 20 轮对话历史)
        context_messages = self.memory.get_context_messages()
        messages.extend(context_messages)
        
        # 当前用户消息
        user_message = {"role": "user", "content": text or "这是什么？"}
        
        # 如果有图片，添加到消息中
        if image_base64:
            user_message["images"] = [image_base64]
            print(f"[IMAGE] Size: {len(image_base64)} bytes")
        
        messages.append(user_message)
        
        # 输出完整的 Prompt
        print(f"\n[SYSTEM PROMPT] (first 200 chars):")
        print(f"   {SYSTEM_PROMPT[:200]}...")
        print(f"\n[USER INPUT]:")
        print(f"   \"{text}\"")
        print(f"\n[MODEL PARAMETERS]:")
        print(f"   - Model: {self.model}")
        print(f"   - Temperature: {settings.TEMPERATURE}")
        print(f"   - Max Tokens: {settings.MAX_TOKENS}")
        print(f"   - Timeout: {self.timeout}s")
        
        # 调用 Ollama API
        print(f"\n[REQUEST] Sending to Ollama...")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": settings.TEMPERATURE,
                            "num_predict": settings.MAX_TOKENS
                        }
                    },
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                result = response.json()
                reply = result.get("message", {}).get("content", "...")
                
                # 输出详细的响应信息
                print(f"\n[RESPONSE] Success")
                print(f"   - Status Code: {response.status_code}")
                
                # 输出 token 使用情况（如果有）
                if "eval_count" in result:
                    print(f"   - Generated Tokens: {result.get('eval_count', 0)}")
                if "prompt_eval_count" in result:
                    print(f"   - Prompt Tokens: {result.get('prompt_eval_count', 0)}")
                if "eval_duration" in result:
                    eval_time = result.get('eval_duration', 0) / 1e9  # nanoseconds to seconds
                    print(f"   - Inference Time: {eval_time:.2f}s")
                if "total_duration" in result:
                    total_time = result.get('total_duration', 0) / 1e9
                    print(f"   - Total Time: {total_time:.2f}s")
                
                print(f"\n[AI REPLY] (first 200 chars):")
                print(f"   {reply[:200]}")
                if len(reply) > 200:
                    print(f"   ... (total {len(reply)} chars)")
                
            except httpx.TimeoutException:
                print(f"\n[ERROR] Request Timeout")
                reply = "Sorry... I was thinking too long. (Request Timeout)"
            except httpx.HTTPStatusError as e:
                print(f"\n[ERROR] HTTP Error: {e.response.status_code}")
                reply = f"Something went wrong... (HTTP {e.response.status_code})"
            except Exception as e:
                print(f"\n[ERROR] Exception: {type(e).__name__}: {str(e)}")
                reply = f"I encountered a technical issue. ({type(e).__name__})"
        
        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)
        
        print(f"\n[LATENCY] {latency_ms}ms ({latency_ms/1000:.2f}s)")
        
        # ==================== 存储对话到记忆 ====================
        # 只有成功响应才存入记忆
        if not reply.startswith("Sorry") and not reply.startswith("Something went wrong"):
            self.memory.add_turn(text, reply)
            stats = self.memory.get_stats()
            print(f"[MEMORY] Stored. Working: {stats['working_memory_turns']}/20 turns, Episodic: {stats.get('episodic_count', 0)}")
        
        print("="*60 + "\n")
        
        return reply, latency_ms
    
    async def health_check(self) -> bool:
        """
        检查 Ollama 服务是否可用
        
        Returns:
            bool: Ollama 服务是否正常
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/tags",
                    timeout=5.0
                )
                return response.status_code == 200
            except Exception:
                return False
    
    async def get_loaded_model(self) -> Optional[str]:
        """
        获取当前加载的模型名称
        
        Returns:
            Optional[str]: 模型名称，如果获取失败则返回 None
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/tags",
                    timeout=5.0
                )
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    # 查找目标模型
                    for model in models:
                        if self.model in model.get("name", ""):
                            return model.get("name")
                return None
            except Exception:
                return None


# ==================== 工厂函数 ====================

def get_ai_service() -> BaseAIService:
    """
    获取 AI 服务实例（工厂模式）
    
    当前返回 OllamaService，未来可根据配置返回不同实现。
    
    Returns:
        BaseAIService: AI 服务实例
    """
    # 未来可以根据环境变量选择不同的服务
    # if settings.AI_BACKEND == "openai":
    #     return OpenAIService()
    # elif settings.AI_BACKEND == "deepseek":
    #     return DeepSeekService()
    
    return OllamaService()


# ==================== Future: 其他实现 ====================

# class OpenAIService(BaseAIService):
#     """OpenAI API 实现（未来扩展）"""
#     pass

# class DeepSeekService(BaseAIService):
#     """DeepSeek API 实现（未来扩展）"""
#     pass
