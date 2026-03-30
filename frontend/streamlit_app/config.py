"""
配置模块 - Streamlit 前端配置
"""
import os


# 后端 API 地址
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# API 端点
API_ENDPOINTS = {
    "gap_analysis": "/api/advise/gap-analysis",
}

# 支持的入学年份
SUPPORTED_YEARS = [2021, 2022, 2023, 2024, 2025]

# 页面配置
PAGE_CONFIG = {
    "page_title": "未央书院培养方案缺口分析助手",
    "page_icon": "📚",
    "layout": "wide",
}
