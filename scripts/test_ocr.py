#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR 服务测试脚本

测试用例：使用项目根目录的 "2023012803_undergraduate major_cn.pdf" 作为测试文件

运行方式：
    cd Agent_competition
    python scripts/test_ocr.py

依赖要求：
    pip install paddleocr pdf2image Pillow
    
    注意：pdf2image 需要系统安装 poppler
      - Windows: 下载 poppler 并添加到 PATH，或修改 POPPLER_PATH
      - macOS: brew install poppler  
      - Linux: apt-get install poppler-utils
"""

import os
import sys

# 添加项目根目录到 Python 路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.services.ocr_service import OCRService, OCRServiceError
from backend.utils.file_utils import validate_pdf_file


# 配置
TEST_PDF_FILENAME = "2023012803_undergraduate major_cn.pdf"
TEST_PDF_PATH = os.path.join(PROJECT_ROOT, TEST_PDF_FILENAME)

# Windows 用户：如果 poppler 不在 PATH 中，请指定路径
# 例如: POPPLER_PATH = r"C:\poppler\Library\bin"
POPPLER_PATH = None


def check_test_file() -> bool:
    """检查测试文件是否存在"""
    print(f"检查测试文件: {TEST_PDF_PATH}")
    try:
        validate_pdf_file(TEST_PDF_PATH)
        print(f"✓ 测试文件存在且有效")
        file_size = os.path.getsize(TEST_PDF_PATH)
        print(f"  文件大小: {file_size / 1024:.1f} KB")
        return True
    except FileNotFoundError:
        print(f"✗ 测试文件不存在: {TEST_PDF_PATH}")
        print(f"  请确保文件 {TEST_PDF_FILENAME} 在项目根目录中")
        return False
    except ValueError as e:
        print(f"✗ 测试文件无效: {e}")
        return False


def test_ocr_service():
    """测试 OCR 服务"""
    print("\n" + "=" * 60)
    print("测试 OCR 服务")
    print("=" * 60)
    
    # 检查测试文件
    if not check_test_file():
        print("\n测试中止：缺少测试文件")
        return False
    
    # 初始化 OCR 服务
    print("\n初始化 OCR 服务...")
    print("  (首次运行会自动下载模型，可能需要几分钟)")
    
    try:
        service = OCRService(
            language="ch",
            dpi=300,
            poppler_path=POPPLER_PATH,
            show_log=False  # 设置为 True 可查看详细日志
        )
        print("✓ OCR 服务初始化成功")
    except Exception as e:
        print(f"✗ OCR 服务初始化失败: {e}")
        print("\n可能的原因:")
        print("  1. 依赖未安装: pip install paddleocr pdf2image Pillow")
        print("  2. 缺少 poppler (pdf2image 依赖)")
        print("     - Windows: 下载 poppler 并添加到 PATH")
        print("     - macOS: brew install poppler")
        print("     - Linux: apt-get install poppler-utils")
        return False
    
    # 执行 OCR
    print(f"\n开始 OCR 处理: {TEST_PDF_FILENAME}")
    print("  (这可能需要一些时间，取决于 PDF 页数)")
    
    try:
        markdown = service.extract_pdf_to_markdown(
            pdf_path=TEST_PDF_PATH,
            cleanup=True  # 清理临时文件
        )
        print("✓ OCR 处理完成")
        return markdown
        
    except OCRServiceError as e:
        print(f"✗ OCR 处理失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 未知错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("OCR 服务测试")
    print("=" * 60)
    
    result = test_ocr_service()
    
    if result:
        print("\n" + "=" * 60)
        print("OCR 结果 (Markdown)")
        print("=" * 60)
        print(result)
        
        # 可选：保存结果到文件
        output_file = os.path.join(PROJECT_ROOT, "ocr_test_result.md")
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"\n✓ 结果已保存到: {output_file}")
        except Exception as e:
            print(f"\n! 保存结果失败: {e}")
        
        return 0
    else:
        print("\n" + "=" * 60)
        print("测试失败")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
