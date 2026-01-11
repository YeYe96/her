"""
API 路由模块

定义所有 HTTP 端点，处理请求并返回响应。
业务逻辑委托给 core 层处理，保持路由层简洁。
"""

from fastapi import APIRouter, HTTPException

from config.settings import settings
from core.ai_service import get_ai_service
from models.schemas import ChatRequest, ChatResponse, HealthResponse, SystemStatus

router = APIRouter()

# 获取 AI 服务实例
ai_service = get_ai_service()


@router.get("/", response_model=SystemStatus)
async def root():
    """
    系统状态接口
    
    返回 Amadeus 系统的基本信息和状态。
    """
    return SystemStatus(
        message="Amadeus System Online",
        status="active",
        version=settings.APP_VERSION
    )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    健康检查接口
    
    检查服务及其依赖（Ollama）的健康状态。
    用于监控和负载均衡器健康检查。
    """
    ollama_ok = await ai_service.health_check()
    model_name = None
    
    if ollama_ok and hasattr(ai_service, 'get_loaded_model'):
        model_name = await ai_service.get_loaded_model()
    
    return HealthResponse(
        status="ok" if ollama_ok else "degraded",
        ollama_connected=ollama_ok,
        model_loaded=model_name
    )


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    核心对话接口
    
    接收用户的文本和可选的图片，返回 AI 回复。
    支持多模态输入（文本 + 图片）。
    
    Args:
        request: 聊天请求，包含 text 和可选的 image_base64
        
    Returns:
        ChatResponse: 包含 AI 回复、模型名称和延迟信息
    """
    try:
        # 调用 AI 服务
        reply, latency_ms = await ai_service.chat(
            text=request.text,
            image_base64=request.image_base64
        )
        
        return ChatResponse(
            reply=reply,
            model=settings.MODEL_NAME,
            latency_ms=latency_ms
        )
        
    except Exception as e:
        # 记录错误（生产环境应使用 logging）
        print(f"[Error] Chat endpoint error: {e}")
        
        # 返回友好的错误信息（保持角色）
        return ChatResponse(
            reply="我...我好像遇到了一些技术问题。(System Error)",
            model=settings.MODEL_NAME,
            latency_ms=0
        )
