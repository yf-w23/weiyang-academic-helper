"""通识选修课课组服务

处理通识选修课四大课组（科学、人文、社科、艺术）的课程管理和学分统计。
"""

import re
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple, Any
from pathlib import Path


@dataclass
class GeneralEduCourse:
    """通识选修课课程"""
    code: str
    name: str
    credits: float
    group: str  # 'science', 'humanities', 'social', 'art'


@dataclass
class GroupRequirement:
    """课组学分要求"""
    group_name: str  # 课组名称
    group_key: str   # 课组标识符
    min_credits: float  # 最少修读学分
    courses: List[GeneralEduCourse] = field(default_factory=list)


@dataclass
class GroupCompletion:
    """课组完成情况"""
    group_name: str
    group_key: str
    credits_required: float
    credits_earned: float
    credits_missing: float
    is_complete: bool
    completed_courses: List[Dict[str, Any]]  # 已修课程列表
    available_courses: List[GeneralEduCourse]  # 可选课程列表（未修的）


@dataclass
class GeneralEduAnalysis:
    """通识选修课完整分析结果"""
    total_required: float  # 总学分要求
    total_earned: float    # 已修总学分
    total_missing: float   # 还差多少学分
    group_completions: List[GroupCompletion]
    all_groups_complete: bool  # 所有课组是否都满足最低要求


class GeneralEduService:
    """通识选修课服务"""
    
    # 课组配置
    # 未央书院通识选修课要求：
    # - 总学分要求：11学分
    # - 科学课组：至少3学分（比其他课组多1学分）
    # - 人文、社科、艺术课组：每个至少2学分
    GROUP_CONFIG = {
        'science': {
            'name': '科学课组',
            'file': 'science.md',
            'min_credits': 3.0,  # 未央书院要求：科学课组至少3学分
        },
        'humanities': {
            'name': '人文课组',
            'file': 'Humanities.md',
            'min_credits': 2.0,
        },
        'social': {
            'name': '社科课组',
            'file': 'Social.md',
            'min_credits': 2.0,
        },
        'art': {
            'name': '艺术课组',
            'file': 'Art.md',
            'min_credits': 2.0,
        },
    }
    
    # 通识选修课总学分要求
    TOTAL_REQUIRED_CREDITS = 11.0
    
    def __init__(self):
        self.project_root = self._get_project_root()
        self.general_edu_dir = self.project_root / "generalEdu"
        self._group_courses: Dict[str, List[GeneralEduCourse]] = {}
        self._load_all_groups()
    
    def _get_project_root(self) -> Path:
        """获取项目根目录"""
        current_file = Path(__file__).resolve()
        # backend/services/general_edu_service.py -> project_root
        return current_file.parent.parent.parent
    
    def _load_all_groups(self):
        """加载所有课组的课程"""
        for group_key, config in self.GROUP_CONFIG.items():
            courses = self._parse_group_file(config['file'], group_key)
            self._group_courses[group_key] = courses
    
    def _parse_group_file(self, filename: str, group_key: str) -> List[GeneralEduCourse]:
        """解析课组 Markdown 文件"""
        file_path = self.general_edu_dir / filename
        if not file_path.exists():
            return []
        
        courses = []
        content = file_path.read_text(encoding='utf-8')
        
        # 解析课程表格
        # 表格格式：| 课程号 | 课程名 | 学分 |
        in_table = False
        for line in content.split('\n'):
            line = line.strip()
            
            # 检测表格行
            if line.startswith('|') and '课程号' not in line and '---' not in line:
                cells = [c.strip() for c in line.split('|')[1:-1]]
                if len(cells) >= 3:
                    code = cells[0].strip()
                    name = cells[1].strip()
                    credits_str = cells[2].strip()
                    
                    # 清理课程号中的引号
                    code = code.replace("'", "").replace('"', '')
                    
                    try:
                        credits = float(credits_str) if credits_str else 0.0
                    except ValueError:
                        credits = 0.0
                    
                    if code and name:
                        courses.append(GeneralEduCourse(
                            code=code,
                            name=name,
                            credits=credits,
                            group=group_key
                        ))
        
        return courses
    
    def get_group_courses(self, group_key: str) -> List[GeneralEduCourse]:
        """获取指定课组的所有课程"""
        return self._group_courses.get(group_key, [])
    
    def get_all_courses(self) -> List[GeneralEduCourse]:
        """获取所有通识选修课"""
        all_courses = []
        for courses in self._group_courses.values():
            all_courses.extend(courses)
        return all_courses
    
    def find_course_by_code(self, course_code: str) -> Optional[GeneralEduCourse]:
        """通过课程号查找通识课"""
        course_code = course_code.strip().replace("'", "").replace('"', '')
        for courses in self._group_courses.values():
            for course in courses:
                if course.code == course_code:
                    return course
        return None
    
    def find_course_by_name(self, course_name: str) -> Optional[GeneralEduCourse]:
        """通过课程名查找通识课（模糊匹配）"""
        for courses in self._group_courses.values():
            for course in courses:
                if course.name in course_name or course_name in course.name:
                    return course
        return None
    
    def analyze_completion(
        self,
        completed_courses: List[Dict[str, Any]]
    ) -> GeneralEduAnalysis:
        """
        分析通识选修课完成情况
        
        Args:
            completed_courses: 已修课程列表，每项包含 code, name, credits, grade 等
        
        Returns:
            GeneralEduAnalysis: 分析结果
        """
        group_completions = []
        total_earned = 0.0
        all_complete = True
        
        # 已修课程的课程号集合（用于判断课程是否已修）
        completed_codes = set()
        completed_names = set()
        for c in completed_courses:
            if c.get('code'):
                completed_codes.add(c.get('code').strip())
            if c.get('name'):
                completed_names.add(c.get('name').strip())
        
        for group_key, config in self.GROUP_CONFIG.items():
            group_courses = self._group_courses.get(group_key, [])
            required_credits = config['min_credits']
            
            # 计算该课组已修学分
            earned_credits = 0.0
            group_completed = []
            
            for course in completed_courses:
                if not course.get('is_passed', True):
                    continue
                    
                course_code = course.get('code', '').strip()
                course_name = course.get('name', '').strip()
                course_credits = course.get('credits', 0.0)
                
                # 检查该课程是否属于当前课组
                is_in_group = False
                for ge_course in group_courses:
                    # 课程号匹配
                    if course_code and ge_course.code == course_code:
                        is_in_group = True
                        break
                    # 课程名模糊匹配
                    if course_name and (ge_course.name in course_name or course_name in ge_course.name):
                        is_in_group = True
                        break
                
                if is_in_group:
                    earned_credits += course_credits
                    group_completed.append({
                        'code': course_code,
                        'name': course_name,
                        'credits': course_credits,
                    })
            
            # 该课组未修的课程
            available_courses = []
            for ge_course in group_courses:
                is_completed = False
                for completed in group_completed:
                    if (completed['code'] and ge_course.code == completed['code']) or \
                       (completed['name'] and ge_course.name in completed['name']):
                        is_completed = True
                        break
                if not is_completed:
                    available_courses.append(ge_course)
            
            missing_credits = max(0, required_credits - earned_credits)
            is_complete = earned_credits >= required_credits
            
            if not is_complete:
                all_complete = False
            
            group_completions.append(GroupCompletion(
                group_name=config['name'],
                group_key=group_key,
                credits_required=required_credits,
                credits_earned=earned_credits,
                credits_missing=missing_credits,
                is_complete=is_complete,
                completed_courses=group_completed,
                available_courses=available_courses
            ))
            
            total_earned += earned_credits
        
        total_missing = max(0, self.TOTAL_REQUIRED_CREDITS - total_earned)
        
        return GeneralEduAnalysis(
            total_required=self.TOTAL_REQUIRED_CREDITS,
            total_earned=total_earned,
            total_missing=total_missing,
            group_completions=group_completions,
            all_groups_complete=all_complete
        )
    
    def get_incomplete_groups(
        self,
        analysis: GeneralEduAnalysis
    ) -> List[GroupCompletion]:
        """获取未完成的课组列表"""
        return [g for g in analysis.group_completions if not g.is_complete]
    
    def generate_analysis_report(self, analysis: GeneralEduAnalysis) -> str:
        """生成通识选修课分析报告"""
        lines = ["## 通识选修课完成情况分析", ""]
        
        # 总体情况
        lines.append(f"**总学分要求**: {analysis.total_required} 学分")
        lines.append(f"**已修学分**: {analysis.total_earned} 学分")
        lines.append(f"**剩余学分**: {analysis.total_missing} 学分")
        lines.append("")
        
        # 各课组情况
        lines.append("### 各课组完成情况")
        lines.append("")
        
        for group in analysis.group_completions:
            status = "✅ 已完成" if group.is_complete else "❌ 未完成"
            lines.append(f"**{group.group_name}**: {group.credits_earned}/{group.credits_required} 学分 {status}")
            
            if group.completed_courses:
                lines.append(f"  - 已修课程: {', '.join([c['name'] for c in group.completed_courses])}")
            
            if not group.is_complete:
                lines.append(f"  - 还需: {group.credits_missing} 学分")
            lines.append("")
        
        # 未完成课组建议
        incomplete = self.get_incomplete_groups(analysis)
        if incomplete:
            lines.append("### 选课建议")
            lines.append("")
            for group in incomplete:
                lines.append(f"**{group.group_name}** 还需修读 {group.credits_missing} 学分，建议从以下课程中选择:")
                # 推荐该课组中评分较高的课程（前5门）
                for course in group.available_courses[:5]:
                    lines.append(f"  - {course.name} ({course.credits}学分, 课程号: {course.code})")
                lines.append("")
        
        return "\n".join(lines)


# 全局服务实例
_general_edu_service: Optional[GeneralEduService] = None


def get_general_edu_service() -> GeneralEduService:
    """获取通识课服务实例（单例模式）"""
    global _general_edu_service
    if _general_edu_service is None:
        _general_edu_service = GeneralEduService()
    return _general_edu_service


def analyze_general_edu_completion(
    completed_courses: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    分析通识选修课完成情况的便捷函数
    
    Args:
        completed_courses: 已修课程列表
        
    Returns:
        分析结果字典
    """
    service = get_general_edu_service()
    analysis = service.analyze_completion(completed_courses)
    
    return {
        'total_required': analysis.total_required,
        'total_earned': analysis.total_earned,
        'total_missing': analysis.total_missing,
        'all_groups_complete': analysis.all_groups_complete,
        'groups': [
            {
                'group_name': g.group_name,
                'group_key': g.group_key,
                'credits_required': g.credits_required,
                'credits_earned': g.credits_earned,
                'credits_missing': g.credits_missing,
                'is_complete': g.is_complete,
                'completed_courses': g.completed_courses,
                'available_courses': [
                    {'code': c.code, 'name': c.name, 'credits': c.credits}
                    for c in g.available_courses
                ]
            }
            for g in analysis.group_completions
        ]
    }


def generate_general_edu_report(completed_courses: List[Dict[str, Any]]) -> str:
    """生成通识选修课分析报告的便捷函数"""
    service = get_general_edu_service()
    analysis = service.analyze_completion(completed_courses)
    return service.generate_analysis_report(analysis)
