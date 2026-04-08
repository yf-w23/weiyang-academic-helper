"""智能选课推荐服务"""

import json
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from pathlib import Path

from .prerequisite_graph import PrerequisiteGraph, load_prerequisite_graph
from .course_data_service import CourseDataService


@dataclass
class CourseRecommendation:
    """课程推荐项"""
    course_code: str
    course_name: str
    credits: float
    semester: str
    reason: str  # 推荐理由
    priority_score: float  # 优先级分数（0-100）
    blocking_score: int  # 阻塞系数
    is_required: bool  # 是否必修课
    match_score: float  # 与用户偏好匹配度
    workload: str  # 工作量：轻/中/重
    rating: float  # 课程评分


class RecommendationEngine:
    """选课推荐引擎"""
    
    def __init__(self):
        self.graph = load_prerequisite_graph()
        self.course_data = CourseDataService()
        self.prereq_data = self._load_prerequisites()
        
    def _load_prerequisites(self) -> List[Dict]:
        """加载先修关系数据"""
        data_path = Path(__file__).parent.parent / "data" / "courses" / "prerequisites.json"
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("prerequisites", [])
        except Exception:
            return []
        
    def recommend(
        self,
        gap_result: Dict[str, Any],
        user_preferences: Dict,
        target_semester: str,
        max_credits: float = 25.0
    ) -> List[CourseRecommendation]:
        """
        生成选课推荐
        
        Args:
            gap_result: 缺口分析结果
            user_preferences: 用户偏好 {"interests": ["软件"], "workload": "轻", "time_preference": "上午"}
            target_semester: 目标学期 "2025-2026-1" (秋季) 或 "2025-2026-2" (春季)
            max_credits: 最大学分限制
            
        Returns:
            按优先级排序的推荐课程列表
        """
        # 1. 获取所有可补课程
        available_courses = self._get_missing_courses(gap_result)
        
        # 2. 筛选当前学期开课且先修课满足的课程
        suitable_courses = self._filter_suitable_courses(
            available_courses, 
            gap_result.get("completed_courses", []),
            target_semester
        )
        
        # 3. 计算每门课的优先级分数
        recommendations = []
        for course in suitable_courses:
            score = self._calculate_priority_score(
                course, 
                gap_result, 
                user_preferences
            )
            
            # 获取课程详细信息
            course_info = self.course_data.get_course_by_code(course["code"])
            
            rec = CourseRecommendation(
                course_code=course["code"],
                course_name=course["name"],
                credits=course.get("credits", 0),
                semester=target_semester,
                reason=self._generate_reason(course, score),
                priority_score=score["total"],
                blocking_score=course.get("blocking_score", 0),
                is_required=course.get("is_required", False),
                match_score=score["preference_match"],
                workload=course_info.get("workload", "中") if course_info else "中",
                rating=course_info.get("rating", 0) if course_info else 0
            )
            recommendations.append(rec)
        
        # 4. 按优先级排序
        recommendations.sort(key=lambda x: x.priority_score, reverse=True)
        
        # 5. 根据学分限制截取
        selected_recs = []
        total_credits = 0
        for rec in recommendations:
            if total_credits + rec.credits <= max_credits:
                selected_recs.append(rec)
                total_credits += rec.credits
        
        return selected_recs
        
    def _get_missing_courses(self, gap_result: Dict[str, Any]) -> List[Dict]:
        """从缺口分析结果获取所有待补课程"""
        missing_courses = []
        
        # 获取未修必修课
        for course in gap_result.get("missing_required_courses", []):
            course["is_required"] = True
            missing_courses.append(course)
        
        # 获取各课组的缺口课程
        for group_gap in gap_result.get("group_gaps", []):
            for course in group_gap.get("missing_courses", []):
                if course not in missing_courses:
                    course["is_required"] = False
                    course["group"] = group_gap.get("group_name", "")
                    missing_courses.append(course)
        
        # 添加阻塞系数
        for course in missing_courses:
            code = course.get("code")
            if code and code in self.graph.nodes:
                course["blocking_score"] = self.graph.nodes[code].blocking_score
            else:
                course["blocking_score"] = 0
        
        return missing_courses
        
    def _filter_suitable_courses(
        self,
        courses: List[Dict],
        completed_courses: List[str],
        target_semester: str
    ) -> List[Dict]:
        """筛选适合本学期修读的课程"""
        suitable = []
        completed_set = set(completed_courses)
        
        # 确定目标学期类型
        if "-1" in target_semester:
            semester_type = "秋季"
        elif "-2" in target_semester:
            semester_type = "春季"
        else:
            semester_type = "全年"
        
        for course in courses:
            code = course.get("code")
            
            # 检查课程是否在培养方案的图里
            if code and code in self.graph.nodes:
                node = self.graph.nodes[code]
                
                # 检查先修课是否完成
                prereqs_satisfied = all(
                    prereq in completed_set 
                    for prereq in node.prerequisites
                )
                
                if prereqs_satisfied:
                    # 检查是否在本学期开课
                    if semester_type in node.semester or node.semester == "全年":
                        course["semester"] = node.semester
                        suitable.append(course)
            else:
                # 对于没有先修信息的课程，也推荐
                course_info = self.course_data.get_course_by_code(code) if code else None
                if course_info:
                    course_semester = course_info.get("semester", "未知")
                    if semester_type in course_semester or course_semester == "全年":
                        suitable.append(course)
                else:
                    # 没有学期信息的也默认推荐
                    suitable.append(course)
        
        return suitable
        
    def _calculate_priority_score(
        self,
        course: Dict,
        gap_result: Dict[str, Any],
        user_preferences: Dict
    ) -> Dict[str, float]:
        """
        计算课程优先级分数
        
        权重：
        - 是否必修：40分
        - 阻塞系数：30分
        - 用户偏好匹配：20分
        - 课程评分：10分
        """
        scores = {
            "required": 0,
            "blocking": 0,
            "preference_match": 0,
            "rating": 0,
            "total": 0
        }
        
        # 1. 必修权重（40分）
        if course.get("is_required", False):
            scores["required"] = 40
        
        # 2. 阻塞系数权重（30分）
        blocking = course.get("blocking_score", 0)
        if blocking >= 10:
            scores["blocking"] = 30
        elif blocking >= 5:
            scores["blocking"] = 20
        elif blocking >= 3:
            scores["blocking"] = 15
        elif blocking >= 1:
            scores["blocking"] = 10
        
        # 3. 用户偏好匹配（20分）
        match_score = self._calculate_preference_match(course, user_preferences)
        scores["preference_match"] = match_score * 20
        
        # 4. 课程评分（10分）
        course_info = self.course_data.get_course_by_code(course.get("code"))
        if course_info and course_info.get("rating"):
            rating = course_info.get("rating")
            scores["rating"] = (rating / 5.0) * 10
        
        # 总分
        scores["total"] = (
            scores["required"] + 
            scores["blocking"] + 
            scores["preference_match"] + 
            scores["rating"]
        )
        
        return scores
        
    def _calculate_preference_match(
        self,
        course: Dict,
        preferences: Dict
    ) -> float:
        """
        计算课程与用户偏好匹配度
        基于课程描述和偏好关键词的相似度
        """
        match_score = 0.0
        
        interests = preferences.get("interests", [])
        workload_pref = preferences.get("workload", "")
        
        course_name = course.get("name", "")
        course_info = self.course_data.get_course_by_code(course.get("code"))
        description = course_info.get("description", "") if course_info else ""
        
        # 兴趣匹配
        for interest in interests:
            if interest in course_name or interest in description:
                match_score += 0.5
        
        # 工作量匹配
        if workload_pref and course_info:
            course_workload = course_info.get("workload", "中")
            if workload_pref == course_workload:
                match_score += 0.5
        
        return min(match_score, 1.0)
        
    def _generate_reason(self, course: Dict, score: Dict[str, float]) -> str:
        """生成推荐理由"""
        reasons = []
        
        if course.get("is_required", False):
            reasons.append("必修课")
        
        blocking = course.get("blocking_score", 0)
        if blocking >= 5:
            reasons.append(f"高阻塞系数（{blocking}）")
        elif blocking >= 1:
            reasons.append(f"阻塞系数{blocking}")
        
        if score["preference_match"] > 10:
            reasons.append("符合个人兴趣")
        
        if reasons:
            return "；".join(reasons)
        return "推荐选修"
        
    def generate_recommendation_report(
        self,
        recommendations: List[CourseRecommendation]
    ) -> str:
        """
        生成推荐报告（Markdown格式）
        包含推荐理由、优先级说明
        """
        if not recommendations:
            return "暂无推荐课程。您可能已经完成了所有课程要求！"
        
        lines = ["# 选课推荐", ""]
        
        # 按优先级分组
        high_priority = [r for r in recommendations if r.priority_score >= 70]
        medium_priority = [r for r in recommendations if 40 <= r.priority_score < 70]
        low_priority = [r for r in recommendations if r.priority_score < 40]
        
        if high_priority:
            lines.append("## 高优先级（强烈推荐）")
            lines.append("")
            for i, rec in enumerate(high_priority, 1):
                lines.append(f"{i}. **{rec.course_name}** ({rec.credits}学分)")
                lines.append(f"   - 推荐理由：{rec.reason}")
                lines.append(f"   - 优先级分数：{rec.priority_score:.1f}")
                if rec.rating:
                    lines.append(f"   - 课程评分：{rec.rating:.1f}/5.0")
                lines.append("")
        
        if medium_priority:
            lines.append("## 中优先级（建议选修）")
            lines.append("")
            for i, rec in enumerate(medium_priority, 1):
                lines.append(f"{i}. **{rec.course_name}** ({rec.credits}学分)")
                lines.append(f"   - 推荐理由：{rec.reason}")
                lines.append("")
        
        if low_priority:
            lines.append("## 低优先级（可选）")
            lines.append("")
            for rec in low_priority[:3]:  # 只显示前3个
                lines.append(f"- {rec.course_name} ({rec.credits}学分) - {rec.reason}")
            lines.append("")
        
        # 选课建议
        total_credits = sum(r.credits for r in recommendations)
        lines.append("## 选课建议")
        lines.append(f"")
        lines.append(f"- 本次推荐共 {len(recommendations)} 门课程，合计 {total_credits} 学分")
        lines.append(f"- 建议每学期修读 18-25 学分")
        lines.append(f"- 优先选择高优先级课程，这些课程通常是必修课或阻塞后续课程的关键课程")
        
        return "\n".join(lines)
        
    def get_learning_path(
        self,
        target_course: str,
        completed_courses: List[str]
    ) -> Dict:
        """
        获取到目标课程的学习路径规划
        返回还需要修哪些先修课
        """
        if target_course not in self.graph.nodes:
            return {
                "target": target_course,
                "error": "课程不在知识图谱中"
            }
        
        # 获取所有先修课
        all_prereqs = self.graph.get_prerequisites_for_course(target_course)
        
        # 筛选未修的先修课
        completed_set = set(completed_courses)
        missing_prereqs = [p for p in all_prereqs if p not in completed_set]
        
        # 按学习顺序排序
        sorted_path = []
        for code in self.graph.topological_sort():
            if code in missing_prereqs:
                node = self.graph.nodes.get(code)
                if node:
                    sorted_path.append({
                        "code": code,
                        "name": node.course_name,
                        "credits": node.credits,
                        "semester": node.semester
                    })
        
        return {
            "target": target_course,
            "target_name": self.graph.nodes[target_course].course_name if target_course in self.graph.nodes else "",
            "total_prerequisites": len(all_prereqs),
            "completed_prerequisites": len(all_prereqs) - len(missing_prereqs),
            "missing_prerequisites": missing_prereqs,
            "learning_path": sorted_path,
            "estimated_semesters": len(sorted_path) // 3 + 1  # 粗略估计
        }


def get_recommendation_engine() -> RecommendationEngine:
    """获取推荐引擎实例"""
    return RecommendationEngine()
