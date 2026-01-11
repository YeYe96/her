"""
Amadeus System - FastAPI 应用入口

主应用文件，配置中间件、路由和启动事件。
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from api.routes import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    
    启动时执行初始化，关闭时执行清理。
    """
    # ==================== 启动时 ====================
    print("=" * 50)
    print(f"  {settings.APP_NAME} v{settings.APP_VERSION}")
    print("=" * 50)
    print(f"  Ollama Host: {settings.OLLAMA_HOST}")
    print(f"  Model: {settings.MODEL_NAME}")
    print(f"  Debug Mode: {settings.DEBUG}")
    print("=" * 50)
    print("  El Psy Kongroo.")
    print("=" * 50)
    
    yield  # 应用运行中
    
    # ==================== 关闭时 ====================
    print("Amadeus System Shutting Down...")


# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## Amadeus System API
    
    基于《命运石之门》的 AI 聊天系统，与牧瀬红莉栖对话。
    
    ### 功能
    - 💬 文本对话
    - 📷 图片分析（多模态）
    - 🧠 角色扮演 AI
    
    ### 技术栈
    - FastAPI + Ollama + Qwen3-VL
    """,
    lifespan=lifespan,
    docs_url="/docs",      # Swagger UI
    redoc_url="/redoc",    # ReDoc
)


# ==================== 中间件配置 ====================

# CORS 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发阶段允许所有来源，生产环境应限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 路由注册 ====================

app.include_router(api_router)


# ==================== 开发服务器入口 ====================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
