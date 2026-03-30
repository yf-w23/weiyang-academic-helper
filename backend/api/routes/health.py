"""
健康检查路由
"""
from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """健康检查响应模型"""

    status: str = "ok"
    version: str = "0.1.0"


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check() -> HealthResponse:
    """
    健康检查接口
    
    用于确认服务是否正常运行
    """
    return HealthResponse(status="ok", version="0.1.0")
