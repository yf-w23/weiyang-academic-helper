"""Graduation schema gap calculator service."""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set, Tuple
from datetime import datetime
from difflib import SequenceMatcher

from .general_edu_service import get_general_edu_service, GeneralEduAnalysis


@dataclass
class CourseRequirement:
    """Course requirement definition."""
    code: Optional[str] = None
    name: str = ""
    credits: float = 0.0
    is_required: bool = False
    is_elective: bool = False
    group_path: str = ""


@dataclass
class GroupGap:
    """Course group gap details."""
    group_name: str
    group_path: str
    credits_required: float
    credits_earned: float
    credits_missing: float
    completion_rate: float
    missing_required_courses: List[CourseRequirement]
    elective_deficit: float


@dataclass
class GapAnalysisResult:
    """Complete gap analysis result."""
    year: str
    class_name: str
    analysis_date: str
    
    total_credits_required: float
    total_credits_earned: float
    total_completion_rate: float
    
    group_gaps: List[GroupGap]
    
    missing_required_courses: List[CourseRequirement]
    low_grade_courses: List[Dict[str, Any]]
    
    theory_credits_earned: float
    practice_credits_earned: float
    
    recommended_semester_credits: float
    estimated_graduation_semester: Optional[str]
    
    # 通识选修课分析结果
    general_edu_analysis: Optional[GeneralEduAnalysis] = None


@dataclass
class CourseGroup:
    """Course group definition."""
    name: str
    path: str
    credits_required: float
    required_courses: List[CourseRequirement] = field(default_factory=list)
    elective_credits: float = 0.0


@dataclass
class GraduationSchema:
    """Graduation schema definition."""
    year: str
    class_name: str
    total_credits_required: float
    groups: List[CourseGroup] = field(default_factory=list)


class GapCalculator:
    """Graduation schema gap calculator."""
    
    # Similarity threshold for fuzzy matching
    FUZZY_MATCH_THRESHOLD = 0.85
    
    def calculate(
        self,
        schema: GraduationSchema,
        completed_courses: List[Any]  # ParsedCourse objects
    ) -> GapAnalysisResult:
        """Calculate graduation schema gaps."""
        group_gaps = []
        all_missing_required = []
        low_grade_courses = []
        theory_credits = 0.0
        practice_credits = 0.0
        
        for group in schema.groups:
            group_gap = self._calculate_group_completion(group, completed_courses)
            group_gaps.append(group_gap)
            
            all_missing_required.extend(group_gap.missing_required_courses)
            
            # Estimate theory/practice credits based on course name patterns
            for course in completed_courses:
                if self._is_course_in_group(course, group):
                    if self._is_practice_course(course.name):
                        practice_credits += course.credits
                    else:
                        theory_credits += course.credits
        
        # Identify low grade courses
        low_grade_courses = self._identify_low_grade_courses(completed_courses)
        
        total_credits_earned = sum(
            course.credits for course in completed_courses 
            if course.is_passed
        )
        
        completion_rate = (
            total_credits_earned / schema.total_credits_required 
            if schema.total_credits_required > 0 else 0.0
        )
        
        # Calculate recommended credits per semester
        remaining_credits = schema.total_credits_required - total_credits_earned
        remaining_semesters = self._estimate_remaining_semesters(completed_courses)
        recommended_credits = (
            remaining_credits / remaining_semesters 
            if remaining_semesters > 0 else 0.0
        )
        
        # Estimate graduation semester
        estimated_graduation = self._estimate_graduation_semester(
            completed_courses, remaining_semesters
        )
        
        # 通识选修课分析
        general_edu_service = get_general_edu_service()
        general_edu_analysis = general_edu_service.analyze_completion(
            [c.to_dict() for c in completed_courses if c.is_passed]
        )
        
        return GapAnalysisResult(
            year=schema.year,
            class_name=schema.class_name,
            analysis_date=datetime.now().isoformat(),
            total_credits_required=schema.total_credits_required,
            total_credits_earned=total_credits_earned,
            total_completion_rate=round(completion_rate * 100, 2),
            group_gaps=group_gaps,
            missing_required_courses=all_missing_required,
            low_grade_courses=low_grade_courses,
            theory_credits_earned=theory_credits,
            practice_credits_earned=practice_credits,
            recommended_semester_credits=round(recommended_credits, 1),
            estimated_graduation_semester=estimated_graduation,
            general_edu_analysis=general_edu_analysis,
        )
    
    def _match_course_to_groups(
        self,
        course: Any,  # ParsedCourse
        schema: GraduationSchema
    ) -> List[str]:
        """Match course to corresponding groups."""
        matched_groups = []
        
        for group in schema.groups:
            if self._is_course_in_group(course, group):
                matched_groups.append(group.path)
        
        return matched_groups
    
    def _is_course_in_group(self, course: Any, group: CourseGroup) -> bool:
        """Check if a course belongs to a group."""
        for req in group.required_courses:
            # Exact code match
            if course.code and req.code and course.code == req.code:
                return True
            
            # Fuzzy name match
            if self._fuzzy_match(course.name, req.name):
                return True
        
        return False
    
    def _fuzzy_match(self, str1: str, str2: str) -> bool:
        """Fuzzy string matching using sequence similarity."""
        if not str1 or not str2:
            return False
        
        # Normalize strings
        s1 = self._normalize_string(str1)
        s2 = self._normalize_string(str2)
        
        # Exact match after normalization
        if s1 == s2:
            return True
        
        # Containment check
        if s1 in s2 or s2 in s1:
            return True
        
        # Sequence similarity
        similarity = SequenceMatcher(None, s1, s2).ratio()
        return similarity >= self.FUZZY_MATCH_THRESHOLD
    
    def _normalize_string(self, s: str) -> str:
        """Normalize string for comparison."""
        s = s.lower().strip()
        # Remove common suffixes/prefixes
        s = re.sub(r'[\(\（].*?[\)\）]', '', s)  # Remove parentheses content
        s = re.sub(r'[0-9]', '', s)  # Remove numbers
        s = re.sub(r'\s+', '', s)  # Remove whitespace
        return s
    
    def _calculate_group_completion(
        self,
        group: CourseGroup,
        completed_courses: List[Any]
    ) -> GroupGap:
        """Calculate completion for a single group."""
        credits_earned = 0.0
        missing_required = []
        matched_courses = set()
        
        # Match required courses
        for req in group.required_courses:
            matched = False
            for course in completed_courses:
                if course.name in matched_courses:
                    continue
                    
                if self._match_course_requirement(course, req):
                    if course.is_passed:
                        credits_earned += course.credits
                    matched_courses.add(course.name)
                    matched = True
                    break
            
            if not matched and req.is_required:
                missing_required.append(req)
        
        # Calculate elective deficit
        elective_earned = max(0, credits_earned - sum(
            r.credits for r in group.required_courses if r.is_required
        ))
        elective_deficit = max(0, group.elective_credits - elective_earned)
        
        # Add credits from non-required completed courses that fit the group
        if group.elective_credits > 0:
            for course in completed_courses:
                if course.name not in matched_courses and course.is_passed:
                    if self._is_course_in_group(course, group):
                        credits_earned += course.credits
                        matched_courses.add(course.name)
                        elective_earned += course.credits
                        if elective_earned >= group.elective_credits:
                            break
        
        credits_missing = max(0, group.credits_required - credits_earned)
        completion_rate = (
            credits_earned / group.credits_required 
            if group.credits_required > 0 else 0.0
        )
        
        return GroupGap(
            group_name=group.name,
            group_path=group.path,
            credits_required=group.credits_required,
            credits_earned=credits_earned,
            credits_missing=credits_missing,
            completion_rate=round(completion_rate * 100, 2),
            missing_required_courses=missing_required,
            elective_deficit=elective_deficit,
        )
    
    def _match_course_requirement(
        self, 
        course: Any, 
        req: CourseRequirement
    ) -> bool:
        """Check if a completed course matches a requirement."""
        # Code match
        if course.code and req.code and course.code == req.code:
            return True
        
        # Fuzzy name match
        if self._fuzzy_match(course.name, req.name):
            return True
        
        return False
    
    def _identify_low_grade_courses(
        self,
        completed_courses: List[Any],
        threshold: float = 2.0
    ) -> List[Dict[str, Any]]:
        """Identify courses that can be retaken to improve grades."""
        low_grade_courses = []
        
        for course in completed_courses:
            if course.grade_point < threshold and course.is_passed:
                low_grade_courses.append({
                    "code": course.code,
                    "name": course.name,
                    "credits": course.credits,
                    "grade": course.grade,
                    "grade_point": course.grade_point,
                    "improvement_potential": round(threshold - course.grade_point, 2),
                })
        
        # Sort by improvement potential (descending)
        low_grade_courses.sort(
            key=lambda x: x["improvement_potential"], 
            reverse=True
        )
        
        return low_grade_courses
    
    def _is_practice_course(self, course_name: str) -> bool:
        """Check if a course is a practice/lab course."""
        practice_keywords = [
            "实验", "实践", "实习", "实训", "课程设计",
            "毕业设计", "论文", "综合训练", "社会实践",
            "lab", "experiment", "practice", "internship",
        ]
        name_lower = course_name.lower()
        return any(kw in name_lower for kw in practice_keywords)
    
    def _estimate_remaining_semesters(
        self, 
        completed_courses: List[Any]
    ) -> int:
        """Estimate remaining semesters based on completed courses."""
        if not completed_courses:
            return 8  # Default: 4 years * 2 semesters
        
        # Find the latest semester
        latest_semester = ""
        for course in completed_courses:
            if course.normalized_semester > latest_semester:
                latest_semester = course.normalized_semester
        
        if not latest_semester:
            return 8
        
        # Parse semester (format: YYYY-YYYY-N)
        parts = latest_semester.split("-")
        if len(parts) >= 3:
            current_year = int(parts[1])
            current_term = int(parts[2])
            
            # Assuming graduation in year 4 (typical bachelor)
            # Current: 2023-2024-1, Graduation: 2026-2027-2
            remaining = (4 - (current_year % 4)) * 2
            if current_term == 2:
                remaining -= 1
            
            return max(1, remaining)
        
        return 4  # Default fallback
    
    def _estimate_graduation_semester(
        self,
        completed_courses: List[Any],
        remaining_semesters: int
    ) -> Optional[str]:
        """Estimate graduation semester."""
        if not completed_courses:
            return None
        
        # Find the latest semester
        latest_semester = ""
        for course in completed_courses:
            if course.normalized_semester > latest_semester:
                latest_semester = course.normalized_semester
        
        if not latest_semester:
            return None
        
        parts = latest_semester.split("-")
        if len(parts) >= 3:
            year = int(parts[1])
            term = int(parts[2])
            
            # Calculate graduation semester
            total_terms = remaining_semesters
            while total_terms > 0:
                if term == 1:
                    term = 2
                else:
                    term = 1
                    year += 1
                total_terms -= 1
            
            return f"{year - 1}-{year}-{term}"
        
        return None


def calculate_gaps(
    schema_dict: Dict[str, Any],
    completed_courses: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Convenience function to calculate gaps from dictionaries."""
    # Convert dict to objects
    from .transcript_parser import ParsedCourse
    
    groups = []
    for g in schema_dict.get("groups", []):
        reqs = [
            CourseRequirement(
                code=r.get("code"),
                name=r.get("name", ""),
                credits=r.get("credits", 0.0),
                is_required=r.get("is_required", False),
                is_elective=r.get("is_elective", False),
                group_path=g.get("path", ""),
            )
            for r in g.get("courses", [])
        ]
        groups.append(CourseGroup(
            name=g.get("name", ""),
            path=g.get("path", ""),
            credits_required=g.get("credits_required", 0.0),
            required_courses=reqs,
            elective_credits=g.get("elective_credits", 0.0),
        ))
    
    schema = GraduationSchema(
        year=schema_dict.get("year", ""),
        class_name=schema_dict.get("class_name", ""),
        total_credits_required=schema_dict.get("total_credits_required", 0.0),
        groups=groups,
    )
    
    # Convert completed courses
    courses = [
        ParsedCourse(
            code=c.get("code", ""),
            name=c.get("name", ""),
            credits=c.get("credits", 0.0),
            grade=c.get("grade", ""),
            semester=c.get("semester", ""),
            grade_point=c.get("grade_point", 0.0),
            normalized_grade=c.get("normalized_grade", ""),
            normalized_semester=c.get("normalized_semester", ""),
            is_passed=c.get("is_passed", True),
        )
        for c in completed_courses
    ]
    
    calculator = GapCalculator()
    result = calculator.calculate(schema, courses)
    
    # Convert result to dict
    return {
        "year": result.year,
        "class_name": result.class_name,
        "analysis_date": result.analysis_date,
        "total_credits_required": result.total_credits_required,
        "total_credits_earned": result.total_credits_earned,
        "total_completion_rate": result.total_completion_rate,
        "group_gaps": [
            {
                "group_name": g.group_name,
                "group_path": g.group_path,
                "credits_required": g.credits_required,
                "credits_earned": g.credits_earned,
                "credits_missing": g.credits_missing,
                "completion_rate": g.completion_rate,
                "missing_required_courses": [
                    {
                        "code": c.code,
                        "name": c.name,
                        "credits": c.credits,
                    }
                    for c in g.missing_required_courses
                ],
                "elective_deficit": g.elective_deficit,
            }
            for g in result.group_gaps
        ],
        "missing_required_courses": [
            {
                "code": c.code,
                "name": c.name,
                "credits": c.credits,
            }
            for c in result.missing_required_courses
        ],
        "low_grade_courses": result.low_grade_courses,
        "theory_credits_earned": result.theory_credits_earned,
        "practice_credits_earned": result.practice_credits_earned,
        "recommended_semester_credits": result.recommended_semester_credits,
        "estimated_graduation_semester": result.estimated_graduation_semester,
        "general_edu_analysis": {
            "total_required": result.general_edu_analysis.total_required,
            "total_earned": result.general_edu_analysis.total_earned,
            "total_missing": result.general_edu_analysis.total_missing,
            "all_groups_complete": result.general_edu_analysis.all_groups_complete,
            "groups": [
                {
                    "group_name": g.group_name,
                    "group_key": g.group_key,
                    "credits_required": g.credits_required,
                    "credits_earned": g.credits_earned,
                    "credits_missing": g.credits_missing,
                    "is_complete": g.is_complete,
                    "completed_courses": g.completed_courses,
                }
                for g in result.general_edu_analysis.group_completions
            ]
        } if result.general_edu_analysis else None,
    }
