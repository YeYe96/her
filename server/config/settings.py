"""
应用配置模块 - 符合 4.1 环境变量配置化规范

所有配置均通过环境变量加载，支持开发/生产环境无缝切换。
"""

import os
from typing import Optional
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


class Settings:
    """
    应用配置类
    
    所有值均可通过环境变量覆盖，默认值适用于本地开发环境。
    生产环境部署时，只需修改 .env 文件或设置环境变量即可。
    """
    
    # ==================== Ollama 配置 ====================
    # Ollama 服务地址
    # 本地开发: http://localhost:11434
    # 云端部署: http://ollama-service:11434
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    
    # 使用的模型名称
    MODEL_NAME: str = os.getenv("MODEL_NAME", "qwen3-vl")
    
    # ==================== 服务配置 ====================
    # API 监听地址
    # 0.0.0.0 允许外部访问（Tailscale 需要）
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    
    # API 监听端口
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # 是否开启调试模式
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
    
    # ==================== 模型参数 ====================
    # 温度参数 - 控制回复随机性 (0.0 - 1.0)
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    
    # 最大输出 Token 数
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2048"))
    
    # 请求超时时间（秒）- 视觉模型推理较慢，需要较长超时
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "120"))
    
    # ==================== 应用信息 ====================
    APP_NAME: str = "Amadeus System"
    APP_VERSION: str = "2.0.0"
    
    # ==================== Future: 数据库配置 ====================
    # DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./amadeus.db")
    # REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    def __repr__(self) -> str:
        """打印配置信息（隐藏敏感信息）"""
        return (
            f"Settings(\n"
            f"  OLLAMA_HOST={self.OLLAMA_HOST}\n"
            f"  MODEL_NAME={self.MODEL_NAME}\n"
            f"  API_HOST={self.API_HOST}\n"
            f"  API_PORT={self.API_PORT}\n"
            f"  DEBUG={self.DEBUG}\n"
            f")"
        )


# 全局配置实例 - 单例模式
settings = Settings()
