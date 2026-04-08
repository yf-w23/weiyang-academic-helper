"""
FastAPI 应用入口
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径（支持直接运行此文件）
_current_file = Path(__file__).resolve()
_project_root = _current_file.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import advise, health, chat
from backend.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    # 启动时执行
    print(f"[START] Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # TODO: 初始化数据库连接
    # TODO: 加载OCR模型
    # TODO: 初始化LangGraph
    
    yield
    
    # 关闭时执行
    print(f"[STOP] Shutting down {settings.APP_NAME}")
    
    # TODO: 关闭数据库连接
    # TODO: 清理资源


def create_app() -> FastAPI:
    """
    创建FastAPI应用实例
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="培养方案缺口分析智能体 API",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    
    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )
    
    # 挂载路由
    # 健康检查（无前缀）
    app.include_router(health.router)
    
    # API路由（带前缀）
    app.include_router(advise.router, prefix=settings.API_V1_PREFIX)
    app.include_router(chat.router, prefix=settings.API_V1_PREFIX)
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
