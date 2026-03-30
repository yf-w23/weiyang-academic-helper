"""
OCR 服务模块 - 优先使用 PaddleOCR 云端 API，失败时回退到本地 OCR

使用方式：
    # 自动模式（云端失败时自动回退到本地）
    from backend.services.ocr_service import extract_pdf_to_markdown
    text = extract_pdf_to_markdown("transcript.pdf", auto_fallback=True)
    
    # 强制使用本地 OCR
    from backend.services.ocr_service_local import extract_pdf_to_markdown_local
    text = extract_pdf_to_markdown_local("transcript.pdf")
"""

import os
import sys
from pathlib import Path
from typing import Optional

from backend.config import settings
from backend.services.ocr_service_local import OCRServiceLocal, OCRServiceError as LocalOCRError


class OCRServiceError(Exception):
    """OCR 服务异常基类"""
    pass


class OCRService:
    """
    OCR 服务类 - 优先云端，支持回退到本地
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        access_token: Optional[str] = None,
        timeout: Optional[int] = None,
        poppler_path: Optional[str] = None,
    ):
        """
        初始化 OCR 服务

        Args:
            api_url: PaddleOCR API URL（可选）
            access_token: PaddleOCR Access Token（可选）
            timeout: 请求超时时间（可选）
            poppler_path: poppler 路径（本地 OCR 使用，可选）
        """
        self.api_url = api_url or settings.PADDLEOCR_DOC_PARSING_API_URL
        self.access_token = access_token or settings.PADDLEOCR_ACCESS_TOKEN
        self.timeout = timeout or settings.PADDLEOCR_DOC_PARSING_TIMEOUT
        self.poppler_path = poppler_path or settings.POPPLER_PATH
        
        # 本地 OCR 服务（延迟初始化）
        self._local_service: Optional[OCRServiceLocal] = None

    def _get_local_service(self) -> OCRServiceLocal:
        """获取本地 OCR 服务实例（懒加载）"""
        if self._local_service is None:
            self._local_service = OCRServiceLocal(
                poppler_path=self.poppler_path,
                show_log=False
            )
        return self._local_service

    def _try_cloud_ocr(self, pdf_path: str) -> str:
        """尝试使用云端 OCR"""
        # 添加 paddleocr_doc_parsing 路径
        paddleocr_path = Path(__file__).parent.parent / "paddleocr_doc_parsing" / "scripts"
        if str(paddleocr_path) not in sys.path:
            sys.path.insert(0, str(paddleocr_path))
        
        import lib
        
        # 设置环境变量
        os.environ["PADDLEOCR_DOC_PARSING_API_URL"] = self.api_url
        os.environ["PADDLEOCR_ACCESS_TOKEN"] = self.access_token
        os.environ["PADDLEOCR_DOC_PARSING_TIMEOUT"] = str(self.timeout)
        
        result = lib.parse_document(file_path=str(Path(pdf_path).absolute()))
        
        if not result.get("ok"):
            error = result.get("error", {})
            raise OCRServiceError(
                f"OCR 失败 [{error.get('code')}]: {error.get('message')}"
            )
        
        return result.get("text", "")

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
            auto_fallback: 云端失败时是否自动回退到本地 OCR（默认 True）
            **options: 额外选项

        Returns:
            str: Markdown 格式的成绩单内容

        Raises:
            OCRServiceError: OCR 提取失败且不重试时
        """
        # 首先尝试云端 OCR
        cloud_error = None
        if self.access_token and self.api_url:
            try:
                print(f"[OCR] 尝试使用云端 API...")
                return self._try_cloud_ocr(pdf_path)
            except Exception as e:
                cloud_error = str(e)
                print(f"[OCR] 云端 API 失败: {cloud_error}")
        else:
            print(f"[OCR] 云端 API 未配置，跳过")
        
        # 云端失败，尝试本地 OCR
        if auto_fallback:
            try:
                print(f"[OCR] 回退到本地 OCR...")
                local_service = self._get_local_service()
                return local_service.extract_pdf_to_markdown(pdf_path, **options)
            except Exception as e:
                fallback_error = str(e)
                print(f"[OCR] 本地 OCR 也失败: {fallback_error}")
                raise OCRServiceError(
                    f"OCR 全部失败。云端: {cloud_error}; 本地: {fallback_error}"
                )
        
        # 不重试，直接抛出云端错误
        raise OCRServiceError(f"云端 OCR 失败: {cloud_error}")


# 便捷函数
def extract_pdf_to_markdown(
    pdf_path: str,
    auto_fallback: bool = True,
    **options
) -> str:
    """
    便捷函数：提取 PDF 为 Markdown

    Args:
        pdf_path: PDF 文件路径
        auto_fallback: 云端失败时是否自动回退到本地（默认 True）
        **options: 额外选项

    Returns:
        str: Markdown 格式文本
    """
    service = OCRService()
    return service.extract_pdf_to_markdown(pdf_path, auto_fallback=auto_fallback, **options)
