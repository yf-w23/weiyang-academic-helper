"""
配置模块：读取环境变量与配置
"""
import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent.resolve()

# 手动加载 .env 文件（确保路径正确）
ENV_FILE = ROOT_DIR / ".env"
if ENV_FILE.exists():
    from dotenv import load_dotenv
    load_dotenv(ENV_FILE, override=True)


class Settings(BaseSettings):
    """应用配置类"""

    # 基础配置
    APP_NAME: str = "Course Assistant Agent"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS配置
    CORS_ORIGINS: list[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # API配置
    API_V1_PREFIX: str = "/api"

    # 文件上传配置
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: set[str] = {".pdf"}

    # DeepSeek API 配置
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # PaddleOCR 云端 API 配置
    PADDLEOCR_DOC_PARSING_API_URL: str = "https://paddleocr.com/layout-parsing"
    PADDLEOCR_ACCESS_TOKEN: str = ""
    PADDLEOCR_DOC_PARSING_TIMEOUT: int = 600  # 秒
    
    # 本地 OCR 配置（Windows 可能需要）
    POPPLER_PATH: str = ""  # 例如: C:\poppler\Library\bin

    class Config:
        # 已在模块级别手动加载 .env，此处不需要重复配置
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    """获取配置（带缓存）"""
    return Settings()


settings = get_settings()
