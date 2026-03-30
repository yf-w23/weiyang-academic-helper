# -*- coding: utf-8 -*-
"""
文件处理工具函数
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Optional


def validate_pdf_file(file_path: str) -> bool:
    """
    验证 PDF 文件是否存在且有效
    
    Args:
        file_path: PDF 文件路径
        
    Returns:
        bool: 文件是否有效
        
    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 文件不是 PDF 格式
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    if not path.is_file():
        raise ValueError(f"路径不是文件: {file_path}")
    
    # 检查文件扩展名
    if path.suffix.lower() != '.pdf':
        raise ValueError(f"文件不是 PDF 格式: {file_path}")
    
    # 检查文件大小（PDF 文件至少要有几个字节）
    if path.stat().st_size < 10:
        raise ValueError(f"PDF 文件过小或已损坏: {file_path}")
    
    return True


def get_temp_dir(prefix: str = "ocr_") -> str:
    """
    创建并返回临时目录路径
    
    Args:
        prefix: 临时目录前缀
        
    Returns:
        str: 临时目录路径
    """
    temp_dir = tempfile.mkdtemp(prefix=prefix)
    return temp_dir


def cleanup_temp_files(temp_dir: str) -> bool:
    """
    清理临时文件和目录
    
    Args:
        temp_dir: 临时目录路径
        
    Returns:
        bool: 清理是否成功
    """
    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return True
    except Exception:
        return False


def ensure_dir(directory: str) -> str:
    """
    确保目录存在，不存在则创建
    
    Args:
        directory: 目录路径
        
    Returns:
        str: 目录路径
    """
    os.makedirs(directory, exist_ok=True)
    return directory


def get_file_size(file_path: str) -> int:
    """
    获取文件大小（字节）
    
    Args:
        file_path: 文件路径
        
    Returns:
        int: 文件大小（字节）
    """
    return Path(file_path).stat().st_size


def is_valid_image_file(file_path: str) -> bool:
    """
    检查文件是否为有效的图片格式
    
    Args:
        file_path: 文件路径
        
    Returns:
        bool: 是否为有效图片格式
    """
    valid_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif'}
    path = Path(file_path)
    return path.suffix.lower() in valid_extensions
