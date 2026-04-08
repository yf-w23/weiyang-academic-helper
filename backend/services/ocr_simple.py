"""
简化版 OCR 服务 - 使用 PyMuPDF (fitz) 提取PDF文本
作为 PaddleOCR 云端 API 和本地 PaddleOCR 的轻量级回退方案
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import Optional


class SimpleOCRService:
    """简化版 OCR 服务 - 使用 PyMuPDF 提取文本"""
    
    @staticmethod
    def extract_pdf_to_markdown(pdf_path: str) -> str:
        """
        使用 PyMuPDF 提取 PDF 文本为 Markdown 格式
        
        Args:
            pdf_path: PDF 文件路径
            
        Returns:
            Markdown 格式的文本内容
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")
        
        doc = fitz.open(pdf_path)
        pages_text = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # 提取文本
            text = page.get_text()
            
            # 尝试识别表格（简单启发式方法）
            lines = text.split('\n')
            table_like = any('|' in line or '\t' in line for line in lines[:10])
            
            if table_like:
                # 尝试转换为 Markdown 表格格式
                md_text = SimpleOCRService._convert_to_markdown_table(lines)
            else:
                md_text = text
            
            pages_text.append(f"## 第 {page_num + 1} 页\n\n{md_text}")
        
        doc.close()
        
        # 组合所有页面
        full_text = "\n\n".join(pages_text)
        
        # 添加文件头信息
        header = f"# PDF 成绩单提取结果\n\n"
        header += f"**文件名**: {pdf_path.name}\n\n"
        header += f"**页数**: {len(doc)}\n\n"
        header += "---\n\n"
        
        return header + full_text
    
    @staticmethod
    def _convert_to_markdown_table(lines: list) -> str:
        """尝试将文本行转换为 Markdown 表格"""
        # 过滤空行
        lines = [line.strip() for line in lines if line.strip()]
        
        if len(lines) < 2:
            return "\n".join(lines)
        
        # 检测是否是表格格式（包含制表符或多个空格分隔）
        # 简单处理：如果行中有规律的空格或制表符，尝试分割
        table_rows = []
        for line in lines:
            # 使用多个空格或制表符分割
            parts = [p.strip() for p in line.replace('\t', '  ').split('  ') if p.strip()]
            if len(parts) >= 2:
                table_rows.append(parts)
        
        if len(table_rows) >= 2 and all(len(row) == len(table_rows[0]) for row in table_rows):
            # 转换为 Markdown 表格
            col_count = len(table_rows[0])
            md_lines = []
            
            # 表头
            md_lines.append('| ' + ' | '.join(table_rows[0]) + ' |')
            # 分隔符
            md_lines.append('| ' + ' | '.join(['---'] * col_count) + ' |')
            # 数据行
            for row in table_rows[1:]:
                md_lines.append('| ' + ' | '.join(row) + ' |')
            
            return '\n'.join(md_lines)
        
        # 不是表格格式，返回普通文本
        return "\n".join(lines)


# 便捷函数
def extract_pdf_to_markdown_simple(pdf_path: str) -> str:
    """简化版 PDF 提取函数"""
    service = SimpleOCRService()
    return service.extract_pdf_to_markdown(pdf_path)
