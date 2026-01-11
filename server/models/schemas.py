"""
Pydantic 数据模型定义

定义 API 请求和响应的数据结构，用于自动验证和文档生成。
"""

from typing import Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """聊天请求模型"""
    
    text: str = Field(
        ...,
        description="用户输入的文本内容",
        examples=["你好，红莉栖"]
    )
    image_base64: Optional[str] = Field(
        default=None,
        description="可选的图片数据，Base64 编码的 JPEG/PNG",
        examples=[None, "/9j/4AAQSkZJRg..."]
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "你好，红莉栖，这是什么？",
                "image_base64": None
            }
        }


class ChatResponse(BaseModel):
    """聊天响应模型"""
    
    reply: str = Field(
        ...,
        description="AI 的回复内容"
    )
    model: str = Field(
        ...,
        description="使用的模型名称"
    )
    latency_ms: int = Field(
        ...,
        description="响应延迟（毫秒）"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "reply": "哼...不要随便叫我的名字。有什么事吗？",
                "model": "qwen3-vl",
                "latency_ms": 1523
            }
        }


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    
    status: str = Field(
        default="ok",
        description="服务状态"
    )
    ollama_connected: bool = Field(
        ...,
        description="Ollama 服务连接状态"
    )
    model_loaded: Optional[str] = Field(
        default=None,
        description="当前加载的模型名称"
    )


class SystemStatus(BaseModel):
    """系统状态响应模型"""
    
    message: str = Field(
        default="Amadeus System Online",
        description="系统消息"
    )
    status: str = Field(
        default="active",
        description="系统状态"
    )
    version: str = Field(
        ...,
        description="系统版本"
    )
