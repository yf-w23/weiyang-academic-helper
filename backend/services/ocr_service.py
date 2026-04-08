"""
OCR 服务模块 - 优先使用 PaddleOCR 云端 API，失败时回退到本地 OCR 或简化OCR
"""

import os
import sys
import traceback
from pathlib import Path
from typing import Optional

from backend.config import settings


class OCRServiceError(Exception):
    """OCR 服务异常基类"""
    pass


class OCRService:
    """
    OCR 服务类 - 优先云端，支持回退到本地或简化OCR
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        access_token: Optional[str] = None,
        timeout: Optional[int] = None,
        poppler_path: Optional[str] = None,
    ):
        self.api_url = api_url or settings.PADDLEOCR_DOC_PARSING_API_URL
        self.access_token = access_token or settings.PADDLEOCR_ACCESS_TOKEN
        self.timeout = timeout or settings.PADDLEOCR_DOC_PARSING_TIMEOUT
        self.poppler_path = poppler_path or settings.POPPLER_PATH
        
        self._local_service = None
        self._simple_service = None

    def _try_cloud_ocr(self, pdf_path: str) -> str:
        """尝试使用云端 OCR"""
        paddleocr_path = Path(__file__).parent.parent / "paddleocr_doc_parsing" / "scripts"
        if str(paddleocr_path) not in sys.path:
            sys.path.insert(0, str(paddleocr_path))
        
        # 先设置环境变量（在导入 lib 之前设置，确保 lib 能读取到）
        os.environ["PADDLEOCR_DOC_PARSING_API_URL"] = self.api_url
        os.environ["PADDLEOCR_ACCESS_TOKEN"] = self.access_token
        os.environ["PADDLEOCR_DOC_PARSING_TIMEOUT"] = str(self.timeout)
        
        import lib
        
        # 强制重新加载配置（因为 lib 可能已经加载过了）
        lib._env_loaded = False
        lib._load_env()
        
        print(f"[OCR] Cloud API URL: {self.api_url}")
        print(f"[OCR] Cloud API Token: {self.access_token[:10]}...")
        
        result = lib.parse_document(file_path=str(Path(pdf_path).absolute()))
        
        if not result.get("ok"):
            error = result.get("error", {})
            raise OCRServiceError(
                f"OCR 失败 [{error.get('code')}]: {error.get('message')}"
            )
        
        return result.get("text", "")

    def _try_local_ocr(self, pdf_path: str) -> str:
        """尝试使用本地 PaddleOCR"""
        try:
            from backend.services.ocr_service_local import OCRServiceLocal
            if self._local_service is None:
                self._local_service = OCRServiceLocal(
                    poppler_path=self.poppler_path,
                    show_log=False
                )
            return self._local_service.extract_pdf_to_markdown(pdf_path)
        except ImportError:
            raise OCRServiceError("本地 PaddleOCR 未安装")

    def _try_simple_ocr(self, pdf_path: str) -> str:
        """尝试使用简化版 OCR (PyMuPDF)"""
        try:
            from backend.services.ocr_simple import SimpleOCRService
            if self._simple_service is None:
                self._simple_service = SimpleOCRService()
            return self._simple_service.extract_pdf_to_markdown(pdf_path)
        except ImportError:
            raise OCRServiceError("简化版 OCR (PyMuPDF) 未安装")

    def extract_pdf_to_markdown(
        self,
        pdf_path: str,
        auto_fallback: bool = True,
        **options
    ) -> str:
        """
        将 PDF 成绩单提取为 Markdown

        Args:
            pdf_path: PDF 文件路径
            auto_fallback: 失败时是否自动回退（默认 True）
            **options: 额外选项

        Returns:
            str: Markdown 格式的成绩单内容
        """
        print(f"[OCR] 开始处理文件: {pdf_path}")
        
        errors = []
        
        # 1. 尝试云端 OCR
        if self.access_token and self.api_url:
            # 检查API URL是否有效（不是示例URL）
            is_valid_url = (
                ("paddleocr.com" in self.api_url and "your-service" not in self.api_url) or
                "aistudio-app.com" in self.api_url
            )
            if is_valid_url:
                try:
                    print(f"[OCR] 尝试使用云端 API: {self.api_url}")
                    result = self._try_cloud_ocr(pdf_path)
                    print(f"[OCR] 云端 API 成功")
                    return result
                except Exception as e:
                    error_msg = f"云端 OCR: {str(e)}"
                    print(f"[OCR] {error_msg}")
                    errors.append(error_msg)
            else:
                print(f"[OCR] API URL 看起来是示例地址，跳过云端: {self.api_url}")
        else:
            print(f"[OCR] 云端 API 未配置，跳过")
        
        if not auto_fallback:
            raise OCRServiceError(f"云端 OCR 失败: {'; '.join(errors)}")
        
        # 2. 尝试本地 PaddleOCR
        try:
            print(f"[OCR] 回退到本地 PaddleOCR...")
            result = self._try_local_ocr(pdf_path)
            print(f"[OCR] 本地 PaddleOCR 成功")
            return result
        except Exception as e:
            error_msg = f"本地 PaddleOCR: {str(e)}"
            print(f"[OCR] {error_msg}")
            errors.append(error_msg)
        
        # 3. 尝试简化版 OCR (PyMuPDF)
        try:
            print(f"[OCR] 回退到简化版 OCR (PyMuPDF)...")
            result = self._try_simple_ocr(pdf_path)
            print(f"[OCR] 简化版 OCR 成功")
            return result
        except Exception as e:
            error_msg = f"简化版 OCR: {str(e)}"
            print(f"[OCR] {error_msg}")
            errors.append(error_msg)
            traceback.print_exc()
        
        # 全部失败
        raise OCRServiceError(f"所有 OCR 方式都失败: {'; '.join(errors)}")


# 便捷函数
def extract_pdf_to_markdown(
    pdf_path: str,
    auto_fallback: bool = True,
    **options
) -> str:
    """便捷函数：提取 PDF 为 Markdown"""
    service = OCRService()
    return service.extract_pdf_to_markdown(pdf_path, auto_fallback=auto_fallback, **options)
