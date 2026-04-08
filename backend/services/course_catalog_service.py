#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
课程目录服务类
从 info_courses_md 目录下的 Markdown 文件中解析课程信息，构建结构化课程目录。
"""

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class CourseInfo:
    """单门课程的结构化信息"""

    code: str = ""
    name: str = ""
    hours: int = 0
    credits: float = 0.0
    teacher_id: str = ""
    teacher_name: str = ""
    description: str = ""
    assessment: str = ""
    grading: str = ""
    guidance: str = ""


class CourseCatalogService:
    """课程目录服务，从 Markdown 文件中加载并检索课程数据。"""

    _instance: Optional["CourseCatalogService"] = None

    # ------------------------------------------------------------------
    # Singleton
    # ------------------------------------------------------------------

    def __new__(cls) -> "CourseCatalogService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self._initialized = True
        self._courses: List[CourseInfo] = []
        self._course_by_code: Dict[str, CourseInfo] = {}
        self._courses_by_name: Dict[str, List[CourseInfo]] = {}

        self._load_all_md_files()

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def _load_all_md_files(self) -> None:
        """Load every *.md file in the info_courses_md directory."""
        md_dir = Path(__file__).parent.parent.parent / "info_courses_md"
        if not md_dir.is_dir():
            return

        for md_file in sorted(md_dir.glob("*.md")):
            courses = self._parse_md_file(md_file)
            for course in courses:
                self._courses.append(course)

                # index by code
                if course.code:
                    self._course_by_code[course.code] = course

                # index by name
                if course.name:
                    self._courses_by_name.setdefault(course.name, []).append(course)

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_md_file(path: Path) -> List[CourseInfo]:
        """Parse a single Markdown file and return a list of CourseInfo."""
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return []

        # Split on horizontal rules (---) to isolate each course block.
        blocks = re.split(r"\n---\s*\n", text)

        results: List[CourseInfo] = []
        for block in blocks:
            course = CourseCatalogService._parse_course_block(block)
            if course is not None:
                results.append(course)

        return results

    @staticmethod
    def _parse_course_block(block: str) -> Optional[CourseInfo]:
        """Parse one course block (text between two --- separators)."""
        block = block.strip()

        # A valid course block must start with "## " (course name header).
        # Find the first ## heading which is the course name.
        name_match = re.search(r"^##\s+(.+)$", block, re.MULTILINE)
        if name_match is None:
            return None

        course_name = name_match.group(1).strip()

        # ---- Extract table fields ----
        def _field(label: str) -> str:
            """Return the value cell for a given label in the Markdown table."""
            pattern = rf"\|\s*{re.escape(label)}\s*\|\s*(.*?)\s*\|"
            m = re.search(pattern, block)
            if m is None:
                return ""
            return m.group(1).strip()

        raw_code = _field("课程编号")
        raw_hours = _field("总学时")
        raw_credits = _field("总学分")
        raw_teacher_id = _field("开课教师编号")
        raw_teacher_name = _field("开课教师")

        # Clean quotes from course code
        code = raw_code.strip("'\"") if raw_code else ""

        # Normalize "未知" and blank values
        code = "" if code == "未知" else code
        raw_hours = "" if raw_hours == "未知" else raw_hours
        raw_credits = "" if raw_credits == "未知" else raw_credits
        raw_teacher_id = "" if raw_teacher_id == "未知" else raw_teacher_id
        raw_teacher_name = "" if raw_teacher_name == "未知" else raw_teacher_name

        # Parse numeric fields
        try:
            hours = int(raw_hours) if raw_hours else 0
        except (ValueError, TypeError):
            hours = 0

        try:
            credits = float(raw_credits) if raw_credits else 0.0
        except (ValueError, TypeError):
            credits = 0.0

        # ---- Extract prose sections ----
        def _section(title: str) -> str:
            """Return the text beneath a ### heading, up to the next heading or EOF."""
            pattern = rf"###\s+{re.escape(title)}\s*\n(.*?)(?=\n###|\Z)"
            m = re.search(pattern, block, re.DOTALL)
            if m is None:
                return ""
            text = m.group(1).strip()
            return "" if text == "未知" else text

        description = _section("课程内容简介")
        assessment = _section("考核方式")
        grading = _section("成绩评定标准")
        guidance = _section("选课指导")

        return CourseInfo(
            code=code,
            name=course_name,
            hours=hours,
            credits=credits,
            teacher_id=raw_teacher_id,
            teacher_name=raw_teacher_name,
            description=description,
            assessment=assessment,
            grading=grading,
            guidance=guidance,
        )

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _similarity(a: str, b: str) -> float:
        """Compute similarity ratio between two strings."""
        return SequenceMatcher(None, a, b).ratio()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_course_by_code(self, code: str) -> Optional[CourseInfo]:
        """Look up a course by its exact course code."""
        return self._course_by_code.get(code)

    def get_courses_by_name(self, name: str, fuzzy: bool = False) -> List[CourseInfo]:
        """Look up courses by name.

        When *fuzzy* is True, courses whose names have a SequenceMatcher
        similarity ratio > 0.7 with *name* are also included.
        """
        if not fuzzy:
            return list(self._courses_by_name.get(name, []))

        results: List[CourseInfo] = []
        for course_name, courses in self._courses_by_name.items():
            if name in course_name or course_name in name:
                results.extend(courses)
            elif self._similarity(name, course_name) > 0.7:
                results.extend(courses)
        return results

    def search_courses(self, keyword: str) -> List[CourseInfo]:
        """Search across course name, description, and teacher name."""
        if not keyword:
            return []

        kw = keyword.lower()
        results: List[CourseInfo] = []
        seen_codes: set = set()

        for course in self._courses:
            course_key = course.code or course.name
            if course_key in seen_codes:
                continue

            searchable = " ".join(
                [course.name, course.description, course.teacher_name]
            ).lower()

            if kw in searchable:
                results.append(course)
                if course_key:
                    seen_codes.add(course_key)

        return results

    def get_all_courses(self) -> List[CourseInfo]:
        """Return the full list of courses."""
        return list(self._courses)

    def get_statistics(self) -> dict:
        """Return aggregate statistics about the catalog."""
        total = len(self._courses)

        credits_ranges = {
            "0 credits": 0,
            "1-2 credits": 0,
            "3 credits": 0,
            "4 credits": 0,
            "5+ credits": 0,
        }
        for c in self._courses:
            cr = c.credits
            if cr == 0:
                credits_ranges["0 credits"] += 1
            elif cr <= 2:
                credits_ranges["1-2 credits"] += 1
            elif cr == 3:
                credits_ranges["3 credits"] += 1
            elif cr == 4:
                credits_ranges["4 credits"] += 1
            else:
                credits_ranges["5+ credits"] += 1

        with_code = sum(1 for c in self._courses if c.code)
        with_description = sum(1 for c in self._courses if c.description)
        with_teacher = sum(1 for c in self._courses if c.teacher_name)

        return {
            "total_courses": total,
            "courses_with_code": with_code,
            "courses_with_description": with_description,
            "courses_with_teacher": with_teacher,
            "credits_distribution": credits_ranges,
        }


# ----------------------------------------------------------------------
# Module-level singleton accessor
# ----------------------------------------------------------------------

_catalog_service_instance: Optional[CourseCatalogService] = None


def get_course_catalog_service() -> CourseCatalogService:
    """Return the global CourseCatalogService singleton."""
    global _catalog_service_instance
    if _catalog_service_instance is None:
        _catalog_service_instance = CourseCatalogService()
    return _catalog_service_instance
