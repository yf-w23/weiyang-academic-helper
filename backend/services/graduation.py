"""
Graduation schema service layer.

Business logic for graduation requirements, course extraction, and gap calculation.
"""

import os
from typing import Any


def get_schema_path(year: str, class_name: str) -> str:
    """Return the graduation schema file path for given year and class.
    
    Mapping rule:
        2021级 -> 2021未央书院培养方案.md
        2022级 -> 2022未央书院培养方案.md
        and so on...
    
    Args:
        year: Enrollment year (e.g., "2021", "2022", "2023", "2024", "2025")
        class_name: Class identifier (e.g., "未央-软件11")
        
    Returns:
        Absolute path to the schema markdown file
        
    Raises:
        ValueError: If year is not supported
    """
    # Get project root (parent of backend directory)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    
    # Map year to schema filename
    supported_years = ["2021", "2022", "2023", "2024", "2025"]
    
    if year not in supported_years:
        raise ValueError(
            f"Unsupported year: {year}. "
            f"Supported years: {', '.join(supported_years)}"
        )
    
    filename = f"{year}未央书院培养方案.md"
    # 文件现在存放在 backend/DegreeRequirements/ 目录下
    schema_path = os.path.join(current_dir, "..", "DegreeRequirements", filename)
    schema_path = os.path.normpath(schema_path)
    
    return schema_path


def extract_courses_from_transcript(transcript_md: str) -> list[dict[str, Any]]:
    """Extract completed courses from transcript markdown.
    
    Args:
        transcript_md: Markdown content of transcript
        
    Returns:
        List of course dictionaries with keys like:
        - course_code: Course code
        - course_name: Course name
        - credits: Course credits
        - grade: Course grade/score
        - semester: Semester taken
    """
    # TODO: Implement course extraction logic
    # This would parse the markdown table/format and extract course info
    return []


def calculate_gaps(
    schema_courses: list[dict[str, Any]],
    completed_courses: list[dict[str, Any]]
) -> dict[str, Any]:
    """Calculate gaps between schema requirements and completed courses.
    
    Args:
        schema_courses: List of required courses from schema
        completed_courses: List of completed courses from transcript
        
    Returns:
        Dictionary containing:
        - missing_required: List of missing required courses
        - insufficient_credits: List of course groups with insufficient credits
        - total_credits_earned: Total credits completed
        - total_credits_required: Total credits required
        - completion_rate: Overall completion percentage
    """
    # TODO: Implement gap calculation logic
    # This would compare schema requirements with completed courses
    # and identify missing requirements
    return {
        "missing_required": [],
        "insufficient_credits": [],
        "total_credits_earned": 0,
        "total_credits_required": 0,
        "completion_rate": 0.0,
    }
