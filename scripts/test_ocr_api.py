#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 PaddleOCR 云端 API 连接
"""
import os
import sys

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# 加载 .env
from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

print("=" * 60)
print("PaddleOCR 云端 API 连接测试")
print("=" * 60)

# 检查配置
api_url = os.getenv("PADDLEOCR_DOC_PARSING_API_URL")
token = os.getenv("PADDLEOCR_ACCESS_TOKEN")
timeout = os.getenv("PADDLEOCR_DOC_PARSING_TIMEOUT", "600")

print(f"\n配置信息：")
print(f"  API URL: {api_url}")
print(f"  Token: {token[:10]}...{token[-5:]}" if token and len(token) > 15 else f"  Token: {token}")
print(f"  Timeout: {timeout}s")

if not api_url:
    print("\n❌ 错误: PADDLEOCR_DOC_PARSING_API_URL 未设置")
    sys.exit(1)

if not token:
    print("\n❌ 错误: PADDLEOCR_ACCESS_TOKEN 未设置")
    sys.exit(1)

# 测试文件
TEST_PDF = os.path.join(PROJECT_ROOT, "2023012803_undergraduate major_cn.pdf")
print(f"\n测试文件: {TEST_PDF}")
print(f"文件存在: {os.path.exists(TEST_PDF)}")

# 尝试导入并调用
print("\n" + "-" * 60)
print("尝试调用 PaddleOCR API...")
print("-" * 60)

try:
    # 添加 paddleocr_doc_parsing 路径
    paddleocr_path = os.path.join(PROJECT_ROOT, "backend", "paddleocr_doc_parsing", "scripts")
    if paddleocr_path not in sys.path:
        sys.path.insert(0, paddleocr_path)
    
    import lib
    
    print("✓ 库导入成功")
    
    # 调用 API
    result = lib.parse_document(
        file_path=TEST_PDF,
    )
    
    if result.get("ok"):
        print("✓ API 调用成功")
        text = result.get("text", "")
        print(f"\n提取文本长度: {len(text)} 字符")
        print("\n文本预览（前500字符）：")
        print("-" * 60)
        print(text[:500])
        print("-" * 60)
    else:
        error = result.get("error", {})
        print(f"\n❌ API 调用失败:")
        print(f"  错误码: {error.get('code')}")
        print(f"  错误信息: {error.get('message')}")
        
        # 提供建议
        print("\n可能的原因：")
        if "CONFIG_ERROR" in str(error.get('code')):
            print("  - API URL 或 Token 配置不正确")
        elif "Authentication" in str(error.get('message')):
            print("  - Access Token 无效或已过期")
        elif "disconnected" in str(error.get('message')).lower():
            print("  - 网络连接问题")
            print("  - API URL 不正确（应该指向具体的服务端点）")
            print("\n建议:")
            print("  1. 检查 API URL 是否是正确的服务端点")
            print("  2. 确认 Token 有效且未过期")
            print("  3. 检查网络连接")
        
except Exception as e:
    print(f"\n❌ 发生异常: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
