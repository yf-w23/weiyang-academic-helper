"""Single-turn conversation entry point for gap analysis."""

import os
from typing import Optional

from backend.agent.graph import get_graph, GapAnalysisState
from backend.agent.tools import extract_transcript_from_pdf
from backend.config import settings
from backend.services.transcript_parser import extract_student_info


def run_gap_analysis(
    year: Optional[str] = None,
    class_name: Optional[str] = None,
    pdf_path: Optional[str] = None,
    transcript_md: Optional[str] = None
) -> dict:
    """Run the gap analysis workflow and return results.
    
    This is the main entry point for single-turn gap analysis.
    Can be called from API endpoints or directly.
    
    Args:
        year: Student enrollment year (e.g., "2021"). If not provided, will be
              extracted from the transcript automatically.
        class_name: Class identifier (e.g., "未央-软件11"). If not provided,
                    will be extracted from the transcript automatically.
        pdf_path: Path to transcript PDF (if transcript_md not provided)
        transcript_md: Pre-extracted transcript markdown (if pdf_path not provided)
        
    Returns:
        Dictionary containing:
        - success: bool indicating if analysis completed
        - result: Analysis result string (if success)
        - error: Error message (if not success)
    """
    # Extract from PDF if path provided and no transcript yet
    if pdf_path and not transcript_md:
        try:
            transcript_md = extract_transcript_from_pdf(pdf_path)
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to extract transcript: {str(e)}",
                "result": None
            }
    
    # Validate we have transcript
    if not transcript_md:
        return {
            "success": False,
            "error": "No transcript provided (need pdf_path or transcript_md)",
            "result": None
        }
    
    # Auto-extract year and class_name from transcript if not provided
    if not year or not class_name:
        info = extract_student_info(transcript_md)
        if not year:
            year = info.get("year")
        if not class_name:
            class_name = info.get("class_name")
    
    if not year or not class_name:
        missing = []
        if not year:
            missing.append("入学年份")
        if not class_name:
            missing.append("班级")
        return {
            "success": False,
            "error": f"无法从成绩单中自动识别{ '、'.join(missing) }，请确认上传的是有效的清华大学成绩单",
            "result": None
        }
    
    # Build initial state
    state: GapAnalysisState = {
        "year": year,
        "class_name": class_name,
        "transcript_md": transcript_md,
        "schema_md": None,
        "result": None,
        "error": None,
    }
    
    # Run the graph
    try:
        graph = get_graph()
        final_state = graph.invoke(state)
        
        if final_state.get("error"):
            return {
                "success": False,
                "error": final_state["error"],
                "result": None
            }
        
        return {
            "success": True,
            "result": final_state.get("result"),
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Graph execution failed: {str(e)}",
            "result": None
        }


def run_gap_analysis_with_llm(
    year: Optional[str] = None,
    class_name: Optional[str] = None,
    pdf_path: Optional[str] = None,
    transcript_md: Optional[str] = None
) -> dict:
    """Run gap analysis with actual LLM call.
    
    This is an enhanced version that calls the LLM API for analysis.
    Requires OPENAI_API_KEY to be set.
    
    Args:
        year: Student enrollment year
        class_name: Class identifier
        pdf_path: Path to transcript PDF
        transcript_md: Pre-extracted transcript markdown
        
    Returns:
        Dictionary with analysis results
    """
    # First run the basic workflow to get schema and transcript
    result = run_gap_analysis(year, class_name, pdf_path, transcript_md)
    
    if not result.get("success"):
        return result
    
    # TODO: Call LLM API for actual analysis
    # This would use langchain or direct OpenAI API call
    # For now, return the basic result
    
    return result
