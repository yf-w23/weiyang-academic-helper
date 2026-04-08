"""Transcript OCR text parser service."""

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path


@dataclass
class ParsedCourse:
    """Parsed course data structure."""
    code: str
    name: str
    credits: float
    grade: str
    semester: str
    grade_point: float = 0.0
    normalized_grade: str = ""
    normalized_semester: str = ""
    is_passed: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "code": self.code,
            "name": self.name,
            "credits": self.credits,
            "grade": self.grade,
            "semester": self.semester,
            "grade_point": self.grade_point,
            "normalized_grade": self.normalized_grade,
            "normalized_semester": self.normalized_semester,
            "is_passed": self.is_passed,
        }


class TranscriptParser:
    """Transcript OCR text parser.
    
    Supports multiple transcript formats:
    - Markdown table format
    - Text list format
    - Mixed format
    
    Features:
    - Auto-correct OCR errors (e.g., "A -" -> "A-")
    - Supports letter and percentage grade conversion
    - Normalizes semester format
    """
    
    GRADE_TO_POINT: Dict[str, float] = {
        "A+": 4.0, "A": 4.0, "A-": 3.7,
        "B+": 3.3, "B": 3.0, "B-": 2.7,
        "C+": 2.3, "C": 2.0, "C-": 1.7,
        "D+": 1.3, "D": 1.0, "D-": 0.7,
        "F": 0.0,
        "P": 4.0,
        "NP": 0.0,
        "EX": 4.0,
        "W": 0.0,
    }
    
    PASSING_GRADES = {"A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "P", "EX"}
    
    HEADER_MAPPINGS = {
        "课程号": ["课程号", "课程编号", "编号", "代码", "课程代码"],
        "课程名": ["课程名", "课程名称", "名称", "课名"],
        "学分": ["学分", "学时"],
        "成绩": ["成绩", "分数", "得分"],
        "学期": ["学期", "学年学期", "开课学期"],
    }
    
    def __init__(self):
        self._header_pattern = re.compile(r"\|\s*([^|]+)\s*\|")
        self._table_row_pattern = re.compile(r"\|\s*([^|]*)\s*\|")
        
    def parse(self, transcript_md: str) -> List[ParsedCourse]:
        """Parse OCR-extracted transcript markdown into structured course list."""
        courses = []
        tables = self._extract_tables(transcript_md)
        
        for table in tables:
            table_courses = self._parse_table(table)
            courses.extend(table_courses)
        
        if not courses:
            courses = self._parse_text_format(transcript_md)
        
        courses = self._deduplicate_courses(courses)
        return courses
    
    def _extract_tables(self, md_content: str) -> List[str]:
        """Extract all markdown tables."""
        tables = []
        lines = md_content.split("\n")
        current_table = []
        in_table = False
        
        for line in lines:
            line = line.strip()
            if line.startswith("|"):
                current_table.append(line)
                in_table = True
            else:
                if in_table and current_table:
                    if len(current_table) >= 3:
                        tables.append("\n".join(current_table))
                    current_table = []
                in_table = False
        
        if in_table and len(current_table) >= 3:
            tables.append("\n".join(current_table))
        
        return tables
    
    def _parse_table(self, table: str) -> List[ParsedCourse]:
        """Parse a single table."""
        courses = []
        lines = table.strip().split("\n")
        
        if len(lines) < 3:
            return courses
        
        headers = self._parse_header(lines[0])
        if not headers:
            return courses
        
        header_text = " ".join(headers.values()).lower()
        if not any(keyword in header_text for keyword in ["课程", "学分", "成绩"]):
            return courses
        
        for line in lines[2:]:
            row_data = self._parse_row(line, headers)
            if row_data:
                course = self._create_course(row_data)
                if course:
                    courses.append(course)
        
        return courses
    
    def _parse_header(self, header_line: str) -> Dict[int, str]:
        """Parse header line."""
        headers = {}
        cells = self._header_pattern.findall(header_line)
        
        for idx, cell in enumerate(cells):
            cell = cell.strip()
            for standard_name, aliases in self.HEADER_MAPPINGS.items():
                if any(alias in cell for alias in aliases):
                    headers[idx] = standard_name
                    break
            else:
                headers[idx] = cell
        
        return headers
    
    def _parse_row(self, row_line: str, headers: Dict[int, str]) -> Dict[str, str]:
        """Parse data row."""
        cells = self._table_row_pattern.findall(row_line)
        row_data = {}
        
        for idx, col_name in headers.items():
            if idx < len(cells):
                row_data[col_name] = cells[idx].strip()
        
        return row_data
    
    def _create_course(self, row_data: Dict[str, str]) -> Optional[ParsedCourse]:
        """Create course object from row data."""
        code = row_data.get("课程号", "").strip()
        name = row_data.get("课程名", "").strip()
        credits_str = row_data.get("学分", "").strip()
        grade = row_data.get("成绩", "").strip()
        semester = row_data.get("学期", "").strip()
        
        if not name:
            return None
        
        if not credits_str:
            for key in row_data:
                if "学分" in key or "学时" in key:
                    credits_str = row_data[key].strip()
                    break
        
        try:
            credits = float(re.sub(r"[^\d.]", "", credits_str)) if credits_str else 0.0
        except ValueError:
            credits = 0.0
        
        normalized_grade, grade_point = self._normalize_grade(grade)
        
        is_passed = normalized_grade in self.PASSING_GRADES
        if normalized_grade.isdigit():
            is_passed = float(normalized_grade) >= 60
        
        normalized_semester = self._normalize_semester(semester)
        
        return ParsedCourse(
            code=code,
            name=name,
            credits=credits,
            grade=grade,
            semester=semester,
            grade_point=grade_point,
            normalized_grade=normalized_grade,
            normalized_semester=normalized_semester,
            is_passed=is_passed,
        )
    
    def _parse_text_format(self, content: str) -> List[ParsedCourse]:
        """Parse text format transcript."""
        courses = []
        
        pattern = re.compile(
            r"(\d{6,})\s+"
            r"([^\d\n]{2,30})\s+"
            r"(\d+(?:\.\d+)?)\s*学分?\s+"
            r"([A-F][+-]?|\d{1,3})\s+"
            r"(\d{4}[\-春夏秋冬])"
        )
        
        for match in pattern.finditer(content):
            code = match.group(1).strip()
            name = match.group(2).strip()
            credits = float(match.group(3))
            grade = match.group(4).strip()
            semester = match.group(5).strip()
            
            normalized_grade, grade_point = self._normalize_grade(grade)
            normalized_semester = self._normalize_semester(semester)
            
            is_passed = normalized_grade in self.PASSING_GRADES
            if normalized_grade.isdigit():
                is_passed = float(normalized_grade) >= 60
            
            courses.append(ParsedCourse(
                code=code,
                name=name,
                credits=credits,
                grade=grade,
                semester=semester,
                grade_point=grade_point,
                normalized_grade=normalized_grade,
                normalized_semester=normalized_semester,
                is_passed=is_passed,
            ))
        
        return courses
    
    def _deduplicate_courses(self, courses: List[ParsedCourse]) -> List[ParsedCourse]:
        """Deduplicate course list (keep highest grade)."""
        seen = {}
        
        for course in courses:
            key = (course.code, course.name) if course.code else course.name
            
            if key in seen:
                existing = seen[key]
                if course.grade_point > existing.grade_point:
                    seen[key] = course
            else:
                seen[key] = course
        
        return list(seen.values())
    
    def _normalize_grade(self, grade: str) -> Tuple[str, float]:
        """Normalize grade and convert to grade point."""
        if not grade:
            return "", 0.0
        
        grade = self._clean_grade_string(grade)
        
        upper_grade = grade.upper()
        if upper_grade in self.GRADE_TO_POINT:
            return upper_grade, self.GRADE_TO_POINT[upper_grade]
        
        try:
            numeric_grade = float(grade)
            
            if numeric_grade >= 90:
                return str(int(numeric_grade)), 4.0
            elif numeric_grade >= 85:
                return str(int(numeric_grade)), 3.7
            elif numeric_grade >= 82:
                return str(int(numeric_grade)), 3.3
            elif numeric_grade >= 78:
                return str(int(numeric_grade)), 3.0
            elif numeric_grade >= 75:
                return str(int(numeric_grade)), 2.7
            elif numeric_grade >= 72:
                return str(int(numeric_grade)), 2.3
            elif numeric_grade >= 68:
                return str(int(numeric_grade)), 2.0
            elif numeric_grade >= 64:
                return str(int(numeric_grade)), 1.5
            elif numeric_grade >= 60:
                return str(int(numeric_grade)), 1.0
            else:
                return str(int(numeric_grade)), 0.0
        except ValueError:
            pass
        
        return grade, 0.0
    
    def _clean_grade_string(self, grade: str) -> str:
        """Clean grade string, fix OCR errors."""
        if not grade:
            return ""
        
        grade = grade.strip()
        
        corrections = {
            "A -": "A-",
            "A +": "A+",
            "B -": "B-",
            "B +": "B+",
            "C -": "C-",
            "C +": "C+",
            "D -": "D-",
            "D +": "D+",
            "Ａ": "A",
            "Ｂ": "B",
            "Ｃ": "C",
            "Ｄ": "D",
            "Ｆ": "F",
            "Ｐ": "P",
        }
        
        for wrong, correct in corrections.items():
            grade = grade.replace(wrong, correct)
        
        grade = re.sub(r"\s+", "", grade)
        
        return grade
    
    def _normalize_semester(self, semester: str) -> str:
        """Normalize semester format."""
        if not semester:
            return ""
        
        semester = semester.strip()
        
        if re.match(r"\d{4}-\d{4}-[12]", semester):
            return semester
        
        pattern = re.compile(r"(\d{4})\s*([春秋]|autumn|spring|fall|fa|sp)", re.IGNORECASE)
        match = pattern.search(semester)
        
        if match:
            year = int(match.group(1))
            term_indicator = match.group(2).lower()
            
            if term_indicator in ["秋", "autumn", "fall", "fa"]:
                return f"{year}-{year + 1}-1"
            elif term_indicator in ["春", "spring", "sp"]:
                return f"{year - 1}-{year}-2"
        
        pattern2 = re.compile(r"(\d{4})-?(\d{4})-?([12])")
        match2 = pattern2.search(semester)
        
        if match2:
            year1 = match2.group(1)
            year2 = match2.group(2)
            term = match2.group(3)
            return f"{year1}-{year2}-{term}"
        
        return semester


def parse_transcript(transcript_md: str) -> List[Dict[str, Any]]:
    """Convenience function: parse transcript and return dict list."""
    parser = TranscriptParser()
    courses = parser.parse(transcript_md)
    return [course.to_dict() for course in courses]


def parse_transcript_file(file_path: str) -> List[Dict[str, Any]]:
    """Convenience function: parse transcript from file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    content = path.read_text(encoding="utf-8")
    return parse_transcript(content)


def extract_student_info(transcript_md: str) -> Dict[str, Optional[str]]:
    """Extract enrollment year and class name from transcript markdown.
    
    Supports Tsinghua University transcript format.
    
    Args:
        transcript_md: OCR-extracted transcript markdown text
        
    Returns:
        Dictionary with keys:
        - year: Enrollment year (e.g., "2023") or None
        - class_name: Class identifier (e.g., "未央-电31") or None
    """
    year: Optional[str] = None
    class_name: Optional[str] = None
    
    # Primary: extract year from admission date like "2023年08月入学"
    m = re.search(r"(\d{4})年\s*\d{1,2}月\s*入学", transcript_md)
    if m:
        year = m.group(1)
    
    # Fallback: extract year from student ID (first 4 digits after 学号)
    if not year:
        m = re.search(r"学号\s*(\d{4})", transcript_md)
        if m:
            year = m.group(1)
    
    # Extract class name, e.g., 未央-电31, 未央-软件11, 未央-机械31
    m = re.search(r"(未央-[\u4e00-\u9fa5]+\d{2,3})", transcript_md)
    if m:
        class_name = m.group(1)
    
    return {"year": year, "class_name": class_name}
