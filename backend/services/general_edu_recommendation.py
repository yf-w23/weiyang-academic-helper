"""通识选修课推荐服务

结合课组要求、课程评分和学生偏好，推荐合适的通识选修课。
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from pathlib import Path

from .general_edu_service import get_general_edu_service, GeneralEduAnalysis, GroupCompletion


@dataclass
class CourseRating:
    """课程评分数据"""
    course_code: str
    course_name: str
    teacher_name: str
    department: str
    avg_score: float  # 平均分（百分制）
    grade: str  # 等级（A+, A, A-等）
    total_students: int
    recommendation_score: float = 0.0  # 推荐度计算分数


@dataclass
class GeneralEduRecommendation:
    """通识课推荐项"""
    course_code: str
    course_name: str
    credits: float
    group_name: str  # 所属课组
    group_key: str
    teacher_name: str
    department: str
    rating: float  # 课程评分
    grade: str
    reason: str  # 推荐理由
    priority: int  # 优先级（1-5，1最高）


class CourseRatingService:
    """课程评分数据服务"""
    
    def __init__(self):
        self.project_root = self._get_project_root()
        self.ratings_dir = self.project_root / "info_courses_stars"
        self._ratings: Dict[str, CourseRating] = {}
        self._load_ratings()
    
    def _get_project_root(self) -> Path:
        """获取项目根目录"""
        current_file = Path(__file__).resolve()
        return current_file.parent.parent.parent
    
    def _load_ratings(self):
        """加载课程评分数据"""
        # 支持多个学期的评分文件
        rating_files = [
            "2025-2026秋季学期课程推荐度.md",
            "2025-2026春季学期课程推荐度.md",
        ]
        
        for filename in rating_files:
            file_path = self.ratings_dir / filename
            if file_path.exists():
                self._parse_rating_file(file_path)
    
    def _parse_rating_file(self, file_path: Path):
        """解析评分文件"""
        content = file_path.read_text(encoding='utf-8')
        
        # 解析表格
        # 格式：| 开课院系 | 教师名 | 课程号 | 课程名 | 总人数 | 平均分 | 标准差 | 百分制 | 等级 |
        in_table = False
        for line in content.split('\n'):
            line = line.strip()
            
            if line.startswith('|') and '开课院系' not in line and '---' not in line:
                cells = [c.strip() for c in line.split('|')[1:-1]]
                if len(cells) >= 9:
                    try:
                        department = cells[0]
                        teacher = cells[1]
                        code = cells[2].replace("'", "").replace('"', '')
                        name = cells[3]
                        total = int(cells[4]) if cells[4].isdigit() else 0
                        avg_score = float(cells[7]) if cells[7] else 0.0  # 百分制
                        grade = cells[8]
                        
                        # 使用课程号作为主键，如果有重复取评分高的
                        key = code
                        if key in self._ratings:
                            if avg_score > self._ratings[key].avg_score:
                                self._ratings[key] = CourseRating(
                                    course_code=code,
                                    course_name=name,
                                    teacher_name=teacher,
                                    department=department,
                                    avg_score=avg_score,
                                    grade=grade,
                                    total_students=total
                                )
                        else:
                            self._ratings[key] = CourseRating(
                                course_code=code,
                                course_name=name,
                                teacher_name=teacher,
                                department=department,
                                avg_score=avg_score,
                                grade=grade,
                                total_students=total
                            )
                    except (ValueError, IndexError):
                        continue
    
    def get_rating(self, course_code: str) -> Optional[CourseRating]:
        """获取课程评分"""
        code = course_code.strip().replace("'", "").replace('"', '')
        return self._ratings.get(code)
    
    def get_rating_by_name(self, course_name: str) -> Optional[CourseRating]:
        """通过课程名获取评分（模糊匹配）"""
        for rating in self._ratings.values():
            if rating.course_name in course_name or course_name in rating.course_name:
                return rating
        return None
    
    def get_all_ratings(self) -> List[CourseRating]:
        """获取所有评分数据"""
        return list(self._ratings.values())


class GeneralEduRecommendationEngine:
    """通识选修课推荐引擎"""
    
    def __init__(self):
        self.general_edu_service = get_general_edu_service()
        self.rating_service = CourseRatingService()
    
    def recommend(
        self,
        completed_courses: List[Dict[str, Any]],
        user_preferences: Optional[Dict] = None,
        max_recommendations_per_group: int = 3
    ) -> List[GeneralEduRecommendation]:
        """
        生成通识选修课推荐
        
        Args:
            completed_courses: 已修课程列表
            user_preferences: 用户偏好，如 {"interests": ["人工智能"], "avoid_teachers": ["某某"], "target_group": "art"}
            max_recommendations_per_group: 每个课组最多推荐几门课
            
        Returns:
            推荐课程列表，按优先级排序
        """
        if user_preferences is None:
            user_preferences = {}
        
        target_group = user_preferences.get("target_group")
        
        # 分析完成情况
        analysis = self.general_edu_service.analyze_completion(completed_courses)
        
        recommendations = []
        
        # 如果指定了目标课组，只推荐该课组
        if target_group:
            target_group_obj = None
            for group in analysis.group_completions:
                if group.group_key == target_group or group.group_name == target_group:
                    target_group_obj = group
                    break
            
            if target_group_obj:
                group_recs = self._recommend_for_group(
                    target_group_obj,
                    user_preferences,
                    max_recommendations_per_group * 2  # 给目标课组更多名额
                )
                recommendations.extend(group_recs)
        else:
            # 优先推荐未完成课组的课程
            incomplete_groups = self.general_edu_service.get_incomplete_groups(analysis)
            
            for group in incomplete_groups:
                group_recs = self._recommend_for_group(
                    group, 
                    user_preferences,
                    max_recommendations_per_group
                )
                recommendations.extend(group_recs)
            
            # 如果还有余量，从已完成的课组中推荐高评分课程
            if len(recommendations) < 8:
                complete_groups = [g for g in analysis.group_completions if g.is_complete]
                for group in complete_groups:
                    remaining_slots = 8 - len(recommendations)
                    if remaining_slots <= 0:
                        break
                    group_recs = self._recommend_for_group(
                        group,
                        user_preferences,
                        min(2, remaining_slots),
                        only_high_rated=True
                    )
                    recommendations.extend(group_recs)
        
        # 按优先级排序
        recommendations.sort(key=lambda x: (x.priority, -x.rating))
        
        return recommendations
    
    def _recommend_for_group(
        self,
        group: GroupCompletion,
        user_preferences: Dict,
        max_count: int,
        only_high_rated: bool = False
    ) -> List[GeneralEduRecommendation]:
        """为指定课组生成推荐"""
        recommendations = []
        interests = user_preferences.get('interests', [])
        avoid_teachers = user_preferences.get('avoid_teachers', [])
        
        # 候选课程：该课组未修的课程
        candidates = group.available_courses
        
        # 计算每门课的推荐分数
        scored_candidates = []
        for course in candidates:
            # 获取评分信息
            rating = self.rating_service.get_rating(course.code)
            
            if rating is None:
                rating = self.rating_service.get_rating_by_name(course.name)
            
            # 如果没有评分数据，给默认分数
            if rating is None:
                score = 70.0  # 默认中等分数
                teacher = "未知"
                department = "未知"
                grade = "未知"
            else:
                score = rating.avg_score
                teacher = rating.teacher_name
                department = rating.department
                grade = rating.grade
            
            # 跳过需要回避的老师
            if any(avoid in teacher for avoid in avoid_teachers):
                continue
            
            # 兴趣匹配加分
            interest_bonus = 0
            if interests:
                for interest in interests:
                    if interest in course.name or interest in course.name.lower():
                        interest_bonus = 10
                        break
            
            final_score = score + interest_bonus
            
            scored_candidates.append({
                'course': course,
                'rating': rating,
                'score': final_score,
                'teacher': teacher,
                'department': department,
                'grade': grade
            })
        
        # 按分数排序
        scored_candidates.sort(key=lambda x: x['score'], reverse=True)
        
        # 筛选高评分课程（如果需要）
        if only_high_rated:
            scored_candidates = [c for c in scored_candidates if c['score'] >= 90]
        
        # 生成推荐
        for i, candidate in enumerate(scored_candidates[:max_count]):
            course = candidate['course']
            
            # 生成推荐理由
            reasons = []
            
            # 课组完成情况说明
            if not group.is_complete:
                # 课组未完成，需要补学分
                reasons.append(f"{group.group_name}还需{group.credits_missing}学分")
            else:
                # 课组已完成，作为额外选修推荐
                reasons.append(f"{group.group_name}已修满，可作为额外选修")
            
            # 课程质量
            if candidate['score'] >= 95:
                reasons.append(f"课程评分优秀({candidate['grade']})")
            elif candidate['score'] >= 90:
                reasons.append(f"课程评分良好({candidate['grade']})")
            elif candidate['score'] >= 85:
                reasons.append(f"课程评分较好({candidate['grade']})")
            
            # 选课热度
            if candidate['rating'] and candidate['rating'].total_students > 50:
                reasons.append(f"选课人数多({candidate['rating'].total_students}人)")
            
            # 兴趣匹配
            if interests:
                for interest in interests:
                    if interest in course.name:
                        reasons.append(f"符合兴趣'{interest}'")
                        break
            
            reason = "；".join(reasons) if reasons else "推荐选修"
            
            rec = GeneralEduRecommendation(
                course_code=course.code,
                course_name=course.name,
                credits=course.credits,
                group_name=group.group_name,
                group_key=group.group_key,
                teacher_name=candidate['teacher'],
                department=candidate['department'],
                rating=candidate['score'],
                grade=candidate['grade'],
                reason=reason,
                priority=1 if not group.is_complete else 3
            )
            recommendations.append(rec)
        
        return recommendations
    
    def generate_recommendation_report(
        self,
        recommendations: List[GeneralEduRecommendation]
    ) -> str:
        """生成推荐报告"""
        if not recommendations:
            return "暂无通识课推荐。您可能已经完成了所有通识课要求！"
        
        lines = ["# 通识选修课推荐", ""]
        
        # 按课组分组
        groups = {}
        for rec in recommendations:
            if rec.group_name not in groups:
                groups[rec.group_name] = []
            groups[rec.group_name].append(rec)
        
        # 优先级排序
        priority_names = {1: "高优先级（强烈建议）", 2: "中优先级（建议选修）", 3: "低优先级（可选）"}
        
        for priority in [1, 2, 3]:
            priority_recs = [r for r in recommendations if r.priority == priority]
            if priority_recs:
                lines.append(f"## {priority_names.get(priority, '推荐课程')}")
                lines.append("")
                
                for rec in priority_recs:
                    lines.append(f"### {rec.course_name}")
                    lines.append(f"- **课程号**: {rec.course_code}")
                    lines.append(f"- **学分**: {rec.credits}")
                    lines.append(f"- **所属课组**: {rec.group_name}")
                    lines.append(f"- **开课院系**: {rec.department}")
                    lines.append(f"- **任课教师**: {rec.teacher_name}")
                    if rec.rating > 0:
                        lines.append(f"- **课程评分**: {rec.rating:.1f} ({rec.grade})")
                    lines.append(f"- **推荐理由**: {rec.reason}")
                    lines.append("")
        
        # 选课建议
        total_credits = sum(r.credits for r in recommendations)
        lines.append("## 选课建议")
        lines.append("")
        lines.append(f"- 本次推荐共 {len(recommendations)} 门课程，合计 {total_credits} 学分")
        lines.append("- 通识选修课要求：总学分≥11学分，每个课组至少2学分")
        lines.append("- 建议优先选择高优先级课程，以满足课组最低学分要求")
        lines.append("- 课程评分数据来自往届学生评教，仅供参考")
        
        return "\n".join(lines)


# 便捷函数
_recommendation_engine: Optional[GeneralEduRecommendationEngine] = None


def get_recommendation_engine() -> GeneralEduRecommendationEngine:
    """获取推荐引擎实例"""
    global _recommendation_engine
    if _recommendation_engine is None:
        _recommendation_engine = GeneralEduRecommendationEngine()
    return _recommendation_engine


def recommend_general_edu_courses(
    completed_courses: List[Dict[str, Any]],
    user_preferences: Optional[Dict] = None,
    target_group: Optional[str] = None,
    max_recommendations: int = 10
) -> Dict[str, Any]:
    """
    推荐通识选修课的便捷函数
    
    Args:
        completed_courses: 已修课程列表
        user_preferences: 用户偏好
        target_group: 指定课组，如 "art", "science", "humanities", "social"
        max_recommendations: 最多推荐课程数
        
    Returns:
        包含推荐结果的字典
    """
    if user_preferences is None:
        user_preferences = {}
    
    # 如果指定了目标课组，添加到 preferences
    if target_group:
        user_preferences["target_group"] = target_group
    
    engine = get_recommendation_engine()
    recommendations = engine.recommend(
        completed_courses,
        user_preferences,
        max_recommendations_per_group=3
    )
    
    return {
        'recommendations': [
            {
                'course_code': r.course_code,
                'course_name': r.course_name,
                'credits': r.credits,
                'group_name': r.group_name,
                'group_key': r.group_key,
                'teacher_name': r.teacher_name,
                'department': r.department,
                'rating': r.rating,
                'grade': r.grade,
                'reason': r.reason,
                'priority': r.priority
            }
            for r in recommendations[:max_recommendations]
        ],
        'total_count': len(recommendations),
        'report': engine.generate_recommendation_report(recommendations[:max_recommendations])
    }


def analyze_general_edu_gaps(completed_courses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    分析通识课缺口的便捷函数
    
    Returns:
        缺口分析结果
    """
    service = get_general_edu_service()
    analysis = service.analyze_completion(completed_courses)
    
    incomplete_groups = service.get_incomplete_groups(analysis)
    
    return {
        'total_required': analysis.total_required,
        'total_earned': analysis.total_earned,
        'total_missing': analysis.total_missing,
        'all_complete': analysis.all_groups_complete,
        'incomplete_groups': [
            {
                'group_name': g.group_name,
                'credits_required': g.credits_required,
                'credits_earned': g.credits_earned,
                'credits_missing': g.credits_missing
            }
            for g in incomplete_groups
        ],
        'detailed_analysis': [
            {
                'group_name': g.group_name,
                'is_complete': g.is_complete,
                'credits_earned': g.credits_earned,
                'credits_required': g.credits_required,
                'credits_missing': g.credits_missing,
                'completed_courses': g.completed_courses
            }
            for g in analysis.group_completions
        ]
    }
