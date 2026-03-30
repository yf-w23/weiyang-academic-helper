"""
API 客户端模块 - 与后端 API 通信
"""
import requests
from typing import Dict, Optional

from config import BACKEND_URL, API_ENDPOINTS


def upload_transcript(
    year: int,
    class_name: str,
    pdf_file,
    backend_url: Optional[str] = None
) -> Dict:
    """
    上传成绩单并获取缺口分析结果
    
    Args:
        year: 入学年份
        class_name: 班级名称，如"未央-机械31"
        pdf_file: 上传的 PDF 文件对象
        backend_url: 后端 API 地址（可选，默认使用配置）
    
    Returns:
        dict: 后端返回的分析结果

    Raises:
        requests.RequestException: 请求失败时抛出
    """
    if backend_url is None:
        backend_url = BACKEND_URL
    
    url = f"{backend_url}{API_ENDPOINTS['gap_analysis']}"
    
    # 准备 multipart/form-data
    files = {
        "transcript": (pdf_file.name, pdf_file.getvalue(), "application/pdf")
    }
    data = {
        "enrollment_year": year,
        "class_name": class_name,
    }
    
    try:
        response = requests.post(
            url,
            files=files,
            data=data,
            timeout=120,  # 分析可能需要较长时间
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        raise requests.exceptions.ConnectionError(
            f"无法连接到后端服务器 ({backend_url})，请检查后端服务是否已启动"
        )
    except requests.exceptions.Timeout:
        raise requests.exceptions.Timeout(
            "请求超时，请稍后重试"
        )
    except requests.exceptions.HTTPError as e:
        # 尝试获取错误详情
        try:
            error_detail = response.json().get("detail", str(e))
        except:
            error_detail = str(e)
        raise requests.exceptions.HTTPError(f"分析失败: {error_detail}")


def check_backend_health(backend_url: Optional[str] = None) -> bool:
    """
    检查后端服务是否可用
    
    Args:
        backend_url: 后端 API 地址（可选）
    
    Returns:
        bool: 后端是否可用
    """
    if backend_url is None:
        backend_url = BACKEND_URL
    
    try:
        response = requests.get(f"{backend_url}/health", timeout=5)
        return response.status_code == 200
    except:
        return False
