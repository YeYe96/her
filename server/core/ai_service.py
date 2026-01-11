"""
AI 服务抽象层 - 符合 4.2 接口解耦规范

通过抽象基类封装 AI 调用逻辑，便于未来切换不同的 AI 后端：
- 当前: Ollama (本地)
- 未来: OpenAI, DeepSeek, 通义千问等
"""

import time
import sys
from datetime import datetime
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Optional, Tuple
import httpx

from config.settings import settings
from core.personality import SYSTEM_PROMPT

# 创建日志目录
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"inference_{datetime.now().strftime('%Y%m%d')}.log"

def log_print(message):
    """同时打印到控制台和文件"""
    print(message, flush=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(message + '\n')


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
    """
    
    def __init__(self):
        self.base_url = settings.OLLAMA_HOST
        self.model = settings.MODEL_NAME
        self.timeout = settings.REQUEST_TIMEOUT
        
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
        
        log_print("\n" + "="*60)
        log_print("[AI] Inference Started")
        log_print("="*60)
        
        # 构建消息列表
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        
        # 用户消息
        user_message = {"role": "user", "content": text or "这是什么？"}
        
        # 如果有图片，添加到消息中
        if image_base64:
            user_message["images"] = [image_base64]
            print(f"[IMAGE] Size: {len(image_base64)} bytes", flush=True)
        
        messages.append(user_message)
        
        # 输出完整的 Prompt
        log_print(f"\n[SYSTEM PROMPT] (first 200 chars):")
        log_print(f"   {SYSTEM_PROMPT[:200]}...")
        log_print(f"\n[USER INPUT]:")
        log_print(f"   \"{text}\"")
        log_print(f"\n[MODEL PARAMETERS]:")
        log_print(f"   - Model: {self.model}")
        log_print(f"   - Temperature: {settings.TEMPERATURE}")
        log_print(f"   - Max Tokens: {settings.MAX_TOKENS}")
        log_print(f"   - Timeout: {self.timeout}s")
        
        # 调用 Ollama API
        log_print(f"\n[REQUEST] Sending to Ollama...")
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
                message = result.get("message", {})
                reply = message.get("content", "...")
                thinking = message.get("thinking", None)  # 提取 thinking 字段
                
                # 输出详细的响应信息
                log_print(f"\n[RESPONSE] Success")
                log_print(f"   - Status Code: {response.status_code}")
                
                # 输出 token 使用情况（如果有）
                if "eval_count" in result:
                    log_print(f"   - Generated Tokens: {result.get('eval_count', 0)}")
                if "prompt_eval_count" in result:
                    log_print(f"   - Prompt Tokens: {result.get('prompt_eval_count', 0)}")
                if "eval_duration" in result:
                    eval_time = result.get('eval_duration', 0) / 1e9  # nanoseconds to seconds
                    log_print(f"   - Inference Time: {eval_time:.2f}s")
                if "total_duration" in result:
                    total_time = result.get('total_duration', 0) / 1e9
                    log_print(f"   - Total Time: {total_time:.2f}s")
                
                # 输出 thinking 过程（如果存在）
                if thinking:
                    thinking_lines = thinking.split('\n')
                    thinking_preview_lines = 10  # 控制台预览的行数
                    
                    # 控制台预览（只显示前几行）
                    log_print(f"\n[THINKING PROCESS] (模型思考过程 - 预览):")
                    if len(thinking_lines) > thinking_preview_lines:
                        preview = '\n'.join(thinking_lines[:thinking_preview_lines])
                        log_print(f"   {preview}")
                        log_print(f"   ... (thinking 共 {len(thinking)} 字符, {len(thinking_lines)} 行，完整内容见下方)")
                    else:
                        log_print(f"   {thinking}")
                    
                    # 完整内容写入日志文件（不输出到控制台）
                    with open(LOG_FILE, 'a', encoding='utf-8') as f:
                        f.write(f"\n[THINKING FULL CONTENT] (完整思考过程 - {len(thinking)} 字符, {len(thinking_lines)} 行):\n")
                        f.write("=" * 60 + "\n")
                        for line in thinking_lines:
                            f.write(f"   {line}\n")
                        f.write("=" * 60 + "\n")
                else:
                    log_print(f"\n[THINKING PROCESS]: 未包含 thinking 字段")
                
                log_print(f"\n[AI REPLY] (first 200 chars):")
                log_print(f"   {reply[:200]}")
                if len(reply) > 200:
                    log_print(f"   ... (total {len(reply)} chars)")
                
            except httpx.TimeoutException:
                print(f"\n[ERROR] Request Timeout", flush=True)
                reply = "Sorry... I was thinking too long. (Request Timeout)"
            except httpx.HTTPStatusError as e:
                print(f"\n[ERROR] HTTP Error: {e.response.status_code}", flush=True)
                reply = f"Something went wrong... (HTTP {e.response.status_code})"
            except Exception as e:
                print(f"\n[ERROR] Exception: {type(e).__name__}: {str(e)}", flush=True)
                reply = f"I encountered a technical issue. ({type(e).__name__})"
        
        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)
        
        log_print(f"\n[LATENCY] {latency_ms}ms ({latency_ms/1000:.2f}s)")
        log_print("="*60 + "\n")
        
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
