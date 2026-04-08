#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
课程数据服务类
提供课程数据的查询、搜索等功能
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from difflib import SequenceMatcher


class CourseDataService:
    """课程数据服务类"""
    
    _instance = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._courses = []
        self._course_by_code = {}
        self._course_by_name = {}
        self._schedule = {}
        
        self._load_data()
    
    def _load_data(self):
        """加载课程数据"""
        data_dir = Path(__file__).parent.parent / 'data' / 'courses'
        
        # 加载课程数据
        courses_file = data_dir / 'courses.json'
        if courses_file.exists():
            with open(courses_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._courses = data.get('courses', [])
        
        # 构建索引
        for course in self._courses:
            code = course.get('course_code')
            name = course.get('course_name')
            
            if code:
                self._course_by_code[code] = course
            
            if name:
                if name not in self._course_by_name:
                    self._course_by_name[name] = []
                self._course_by_name[name].append(course)
        
        # 加载开课信息
        schedule_file = data_dir / 'course_schedule.json'
        if schedule_file.exists():
            with open(schedule_file, 'r', encoding='utf-8') as f:
                self._schedule = json.load(f)
    
    def get_course_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """按课程号查询课程"""
        return self._course_by_code.get(code)
    
    def get_course_by_name(self, name: str, fuzzy: bool = False) -> List[Dict[str, Any]]:
        """按课程名查询课程（支持模糊匹配）"""
        if not fuzzy:
            return self._course_by_name.get(name, [])
        
        results = []
        name_lower = name.lower()
        
        for course_name, courses in self._course_by_name.items():
            if name_lower in course_name.lower() or course_name.lower() in name_lower:
                results.extend(courses)
            elif self._similarity(name, course_name) > 0.7:
                results.extend(courses)
        
        return results
    
    def search_courses(self, keyword: str) -> List[Dict[str, Any]]:
        """关键词搜索课程"""
        if not keyword:
            return []
        
        keyword_lower = keyword.lower()
        results = []
        seen_ids = set()
        
        for course in self._courses:
            course_id = course.get('course_code') or course.get('course_name')
            if course_id in seen_ids:
                continue
            
            search_fields = [
                course.get('course_name', ''),
                course.get('course_code', ''),
                course.get('teacher_name', ''),
                course.get('description', ''),
            ]
            
            for field in search_fields:
                if field and keyword_lower in str(field).lower():
                    results.append(course)
                    seen_ids.add(course_id)
                    break
        
        return results
    
    def get_courses_by_semester(self, semester: str) -> List[Dict[str, Any]]:
        """按学期筛选课程"""
        results = []
        semester_map = {
            'spring': ['春季', 'spring'],
            'autumn': ['秋季', 'autumn', 'fall'],
            'all': ['全年', 'all'],
        }
        
        semester_lower = semester.lower()
        valid_terms = []
        
        for terms in semester_map.values():
            if semester_lower in [t.lower() for t in terms]:
                valid_terms.extend(terms)
        
        if not valid_terms:
            valid_terms = [semester]
        
        for course in self._courses:
            course_semester = course.get('semester', '')
            if any(term in course_semester for term in valid_terms):
                results.append(course)
        
        return results
    
    def get_high_rated_courses(self, min_rating: float = 4.0) -> List[Dict[str, Any]]:
        """获取高评分课程"""
        results = []
        
        for course in self._courses:
            rating = course.get('rating')
            if rating is not None and rating >= min_rating:
                results.append(course)
        
        results.sort(key=lambda x: x.get('rating', 0), reverse=True)
        return results
    
    def get_course_rating(self, course_code: str) -> Optional[Dict[str, Any]]:
        """获取课程评分信息"""
        course = self._course_by_code.get(course_code)
        if not course:
            return None
        
        return {
            'course_code': course_code,
            'course_name': course.get('course_name'),
            'rating': course.get('rating'),
            'recommendation_count': course.get('recommendation_count'),
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取数据统计信息"""
        total = len(self._courses)
        with_rating = sum(1 for c in self._courses if c.get('rating') is not None)
        with_code = sum(1 for c in self._courses 
                       if c.get('course_code') and not c.get('course_code', '').startswith('UNKNOWN'))
        
        semester_counts = {}
        for course in self._courses:
            sem = course.get('semester', '未知')
            semester_counts[sem] = semester_counts.get(sem, 0) + 1
        
        return {
            'total_courses': total,
            'courses_with_rating': with_rating,
            'courses_with_code': with_code,
            'semester_distribution': semester_counts,
        }
    
    @staticmethod
    def _similarity(a: str, b: str) -> float:
        """计算两个字符串的相似度"""
        return SequenceMatcher(None, a, b).ratio()


# 全局实例
course_service = CourseDataService()
