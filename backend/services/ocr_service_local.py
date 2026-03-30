"""
OCR 服务模块 - 使用本地 PaddleOCR（备选方案）

安装依赖：
    pip install paddleocr pdf2image pillow
    
    Windows 还需安装 poppler:
    - 下载：https://github.com/oschwartz10612/poppler-windows/releases
    - 解压并添加到 PATH，或在初始化时指定 poppler_path
"""

import os
import re
from pathlib import Path
from typing import List, Tuple, Optional

from backend.utils.file_utils import validate_pdf_file, get_temp_dir, cleanup_temp_files


class OCRServiceError(Exception):
    """OCR 服务异常基类"""
    pass


class OCRServiceLocal:
    """
    本地 OCR 服务类 - 使用 paddleocr + pdf2image
    """

    DEFAULT_LANGUAGE = "ch"
    DEFAULT_DPI = 300

    def __init__(
        self,
        language: str = DEFAULT_LANGUAGE,
        dpi: int = DEFAULT_DPI,
        poppler_path: Optional[str] = None,
        show_log: bool = False
    ):
        """
        初始化本地 OCR 服务
        
        Args:
            language: OCR 语言，默认中文 "ch"
            dpi: PDF 转图片分辨率
            poppler_path: poppler 路径（Windows 可能需要）
            show_log: 是否显示 paddleocr 日志
        """
        try:
            from paddleocr import PaddleOCR
            from pdf2image import convert_from_path
            self._PaddleOCR = PaddleOCR
            self._convert_from_path = convert_from_path
        except ImportError as e:
            raise OCRServiceError(
                f"缺少依赖: {e}\n"
                "请运行: pip install paddleocr pdf2image Pillow\n"
                "Windows 用户还需安装 poppler"
            )
        
        self.language = language
        self.dpi = dpi
        self.poppler_path = poppler_path
        self.show_log = show_log
        
        # 初始化 PaddleOCR（首次会下载模型）
        try:
            self.ocr = PaddleOCR(
                use_angle_cls=True,
                lang=language,
                show_log=show_log
            )
        except Exception as e:
            raise OCRServiceError(f"初始化 PaddleOCR 失败: {e}")

    def extract_pdf_to_markdown(
        self,
        pdf_path: str,
        temp_dir: Optional[str] = None,
        cleanup: bool = True
    ) -> str:
        """
        将 PDF 提取为 Markdown
        
        Args:
            pdf_path: PDF 文件路径
            temp_dir: 临时目录（可选）
            cleanup: 是否清理临时文件
            
        Returns:
            str: Markdown 格式文本
        """
        validate_pdf_file(pdf_path)
        
        # 创建临时目录
        temp_created = False
        if temp_dir is None:
            temp_dir = get_temp_dir(prefix="ocr_local_")
            temp_created = True
        
        try:
            # PDF 转图片
            kwargs = {"dpi": self.dpi}
            if self.poppler_path:
                kwargs["poppler_path"] = self.poppler_path
            
            images = self._convert_from_path(pdf_path, **kwargs)
            
            all_texts = []
            for i, image in enumerate(images, 1):
                # 保存临时图片
                img_path = os.path.join(temp_dir, f"page_{i:03d}.png")
                image.save(img_path, "PNG")
                
                # OCR 识别
                result = self.ocr.ocr(img_path, cls=True)
                
                # 提取文本
                texts = []
                if result and result[0]:
                    for line in result[0]:
                        if line:
                            text = line[1][0]  # 文本内容
                            texts.append(text)
                
                page_text = "\n".join(texts)
                all_texts.append(f"## 第 {i} 页\n\n{page_text}")
            
            return "\n\n".join(all_texts)
            
        except Exception as e:
            raise OCRServiceError(f"OCR 处理失败: {e}")
        finally:
            if cleanup and temp_created:
                cleanup_temp_files(temp_dir)


# 便捷函数
def extract_pdf_to_markdown_local(
    pdf_path: str,
    poppler_path: Optional[str] = None,
    show_log: bool = False
) -> str:
    """
    便捷函数：使用本地 OCR 提取 PDF
    
    Args:
        pdf_path: PDF 文件路径
        poppler_path: poppler 路径（Windows 可能需要）
        show_log: 是否显示日志
        
    Returns:
        str: Markdown 格式文本
    """
    service = OCRServiceLocal(
        poppler_path=poppler_path,
        show_log=show_log
    )
    return service.extract_pdf_to_markdown(pdf_path)
