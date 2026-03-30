"""Tools for the LangGraph agent.

These tools are exposed to the LLM and wrap calls to the services layer.
"""

import os
from typing import Optional

from backend.services.graduation import get_schema_path
from backend.services.ocr_service import extract_pdf_to_markdown


def extract_transcript_from_pdf(pdf_path: str) -> str:
    """Extract transcript content from a PDF file using OCR.
    
    Args:
        pdf_path: Path to the transcript PDF file
        
    Returns:
        Markdown-formatted string containing the extracted transcript content
        
    Raises:
        FileNotFoundError: If the PDF file does not exist
        RuntimeError: If OCR extraction fails
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    # Delegate to OCR service layer
    markdown_content = extract_pdf_to_markdown(pdf_path)
    return markdown_content


def load_graduation_schema(year: str, class_name: str) -> str:
    """Load graduation schema markdown content for given year and class.
    
    Args:
        year: Enrollment year (e.g., "2021", "2022")
        class_name: Class identifier (e.g., "未央-软件11")
        
    Returns:
        Markdown content of the graduation schema file
        
    Raises:
        FileNotFoundError: If schema file does not exist
        ValueError: If year or class_name is invalid
    """
    # Get schema file path from service layer
    schema_path = get_schema_path(year, class_name)
    
    if not os.path.exists(schema_path):
        raise FileNotFoundError(
            f"Graduation schema not found for {year}级 {class_name}: {schema_path}"
        )
    
    # Read and return schema content
    with open(schema_path, "r", encoding="utf-8") as f:
        return f.read()
