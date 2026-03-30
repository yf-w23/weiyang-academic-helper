"""
依赖注入模块
"""
from typing import Generator

from backend.config import Settings, get_settings


def get_config() -> Settings:
    """获取应用配置"""
    return get_settings()


# 预留：数据库会话依赖
def get_db() -> Generator[None, None, None]:
    """获取数据库会话（预留）"""
    # TODO: 后续实现数据库连接
    yield None


# 预留：当前用户依赖
def get_current_user() -> dict | None:
    """获取当前用户（预留）"""
    # TODO: 后续实现用户认证
    return None
