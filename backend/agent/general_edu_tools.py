"""通识选修课相关工具

为 LangGraph Agent 提供通识课分析、推荐等工具函数。
"""

from typing import List, Dict, Optional, Any

from backend.services.general_edu_service import (
    get_general_edu_service,
    analyze_general_edu_completion,
    generate_general_edu_report,
)
from backend.services.general_edu_recommendation import (
    get_recommendation_engine,
    recommend_general_edu_courses,
    analyze_general_edu_gaps,
)


def analyze_general_education_courses(
    completed_courses: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    分析学生通识选修课完成情况
    
    Args:
        completed_courses: 已修课程列表，每项包含:
            - code: 课程号
            - name: 课程名
            - credits: 学分
            - grade: 成绩
            - is_passed: 是否通过
    
    Returns:
        通识课分析结果，包含:
        - total_required: 总学分要求(11学分)
        - total_earned: 已修学分
        - total_missing: 剩余学分
        - all_groups_complete: 是否所有课组都满足最低要求
        - groups: 各课组完成情况详情
    """
    return analyze_general_edu_completion(completed_courses)


def get_general_education_gaps(
    completed_courses: List[Dict[str, Any]]
) -> str:
    """
    获取通识选修课缺口描述（自然语言）
    
    适用于回答"我哪个课组没修满、差几学分"等问题
    
    Args:
        completed_courses: 已修课程列表
        
    Returns:
        自然语言描述的缺口分析
    """
    service = get_general_edu_service()
    analysis = service.analyze_completion(completed_courses)
    
    lines = []
    
    # 总体情况
    lines.append(f"通识选修课总要求: {analysis.total_required} 学分")
    lines.append(f"您已修: {analysis.total_earned} 学分，还差: {analysis.total_missing} 学分")
    lines.append("")
    
    # 各课组情况
    incomplete_groups = []
    for group in analysis.group_completions:
        if group.is_complete:
            lines.append(f"✅ {group.group_name}: 已完成 ({group.credits_earned}/{group.credits_required} 学分)")
        else:
            lines.append(f"❌ {group.group_name}: 未完成 ({group.credits_earned}/{group.credits_required} 学分，还差 {group.credits_missing} 学分)")
            incomplete_groups.append(group)
    
    lines.append("")
    
    # 具体建议
    if incomplete_groups:
        lines.append("**建议优先完成以下课组**:")
        for group in incomplete_groups:
            lines.append(f"- {group.group_name}: 还需修读 {group.credits_missing} 学分")
            if group.available_courses:
                # 推荐几门该课组的课程
                sample_courses = group.available_courses[:3]
                course_names = [f"{c.name}({c.credits}学分)" for c in sample_courses]
                lines.append(f"  可选课程如: {', '.join(course_names)} 等")
    else:
        lines.append("🎉 恭喜！您已完成所有通识课组的最低学分要求。")
        if analysis.total_missing > 0:
            lines.append(f"您还需要修读 {analysis.total_missing} 学分即可满足通识选修课总学分要求。")
    
    return "\n".join(lines)


def recommend_general_education_courses(
    completed_courses: List[Dict[str, Any]],
    interests: Optional[List[str]] = None,
    target_group: Optional[str] = None,
    max_recommendations: int = 8
) -> Dict[str, Any]:
    """
    推荐通识选修课
    
    基于缺口分析、课程评分和用户偏好推荐合适的通识课
    
    Args:
        completed_courses: 已修课程列表
        interests: 用户兴趣标签，如 ["人工智能", "历史", "艺术"]
        target_group: 指定课组，如 "art", "science", "humanities", "social"，如果指定则只推荐该课组
        max_recommendations: 最多推荐课程数
        
    Returns:
        推荐结果，包含推荐列表和报告
    """
    preferences = {"interests": interests or []}
    return recommend_general_edu_courses(
        completed_courses,
        preferences,
        target_group=target_group,
        max_recommendations=max_recommendations
    )


def get_general_education_report(
    completed_courses: List[Dict[str, Any]]
) -> str:
    """
    获取完整的通识选修课分析报告
    
    Args:
        completed_courses: 已修课程列表
        
    Returns:
        Markdown 格式的分析报告
    """
    return generate_general_edu_report(completed_courses)


def query_general_edu_course_info(
    course_name: Optional[str] = None,
    course_code: Optional[str] = None,
    group: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    查询通识选修课信息
    
    Args:
        course_name: 课程名（支持模糊匹配）
        course_code: 课程号
        group: 课组名称，可选 'science', 'humanities', 'social', 'art'
        
    Returns:
        匹配的课程列表
    """
    service = get_general_edu_service()
    results = []
    
    if course_code:
        course = service.find_course_by_code(course_code)
        if course:
            results.append({
                'code': course.code,
                'name': course.name,
                'credits': course.credits,
                'group': course.group,
                'group_name': service.GROUP_CONFIG.get(course.group, {}).get('name', course.group)
            })
    
    elif course_name:
        course = service.find_course_by_name(course_name)
        if course:
            results.append({
                'code': course.code,
                'name': course.name,
                'credits': course.credits,
                'group': course.group,
                'group_name': service.GROUP_CONFIG.get(course.group, {}).get('name', course.group)
            })
    
    elif group:
        courses = service.get_group_courses(group)
        for course in courses:
            results.append({
                'code': course.code,
                'name': course.name,
                'credits': course.credits,
                'group': course.group,
                'group_name': service.GROUP_CONFIG.get(course.group, {}).get('name', course.group)
            })
    
    return results


def get_incomplete_general_edu_groups(
    completed_courses: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    获取未完成的通识课课组列表
    
    Args:
        completed_courses: 已修课程列表
        
    Returns:
        未完成课组列表，包含所需学分信息
    """
    service = get_general_edu_service()
    analysis = service.analyze_completion(completed_courses)
    incomplete = service.get_incomplete_groups(analysis)
    
    return [
        {
            'group_name': g.group_name,
            'group_key': g.group_key,
            'credits_required': g.credits_required,
            'credits_earned': g.credits_earned,
            'credits_missing': g.credits_missing,
            'available_courses': [
                {'code': c.code, 'name': c.name, 'credits': c.credits}
                for c in g.available_courses[:10]  # 返回前10门可选课程
            ]
        }
        for g in incomplete
    ]


def format_general_edu_summary(
    completed_courses: List[Dict[str, Any]]
) -> str:
    """
    格式化通识课完成情况摘要（用于对话回复）
    
    Args:
        completed_courses: 已修课程列表
        
    Returns:
        简洁的摘要文本
    """
    service = get_general_edu_service()
    analysis = service.analyze_completion(completed_courses)
    
    lines = ["**通识选修课完成情况**", ""]
    
    # 总体进度
    progress_pct = (analysis.total_earned / analysis.total_required * 100) if analysis.total_required > 0 else 0
    lines.append(f"总体进度: {analysis.total_earned}/{analysis.total_required} 学分 ({progress_pct:.1f}%)")
    lines.append("")
    
    # 各课组状态
    for group in analysis.group_completions:
        icon = "✅" if group.is_complete else "⚠️"
        lines.append(f"{icon} {group.group_name}: {group.credits_earned:.0f}/{group.credits_required:.0f} 学分")
    
    lines.append("")
    
    # 总结
    if analysis.all_groups_complete:
        if analysis.total_missing <= 0:
            lines.append("🎉 恭喜！您已完成所有通识选修课要求！")
        else:
            lines.append(f"您已完成各课组最低要求，还需修读 {analysis.total_missing:.0f} 学分以满足总学分要求。")
    else:
        incomplete = [g for g in analysis.group_completions if not g.is_complete]
        lines.append(f"您有 {len(incomplete)} 个课组未完成最低学分要求，建议优先补足。")
    
    return "\n".join(lines)
