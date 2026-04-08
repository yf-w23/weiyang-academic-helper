"""测试通识选修课服务"""

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.general_edu_service import (
    get_general_edu_service,
    analyze_general_edu_completion,
    generate_general_edu_report,
)
from backend.services.general_edu_recommendation import (
    recommend_general_edu_courses,
    analyze_general_edu_gaps,
)


def test_service():
    """测试通识课服务"""
    print("=" * 60)
    print("测试通识选修课服务")
    print("=" * 60)
    
    # 1. 测试课程加载
    print("\n1. 测试课程加载")
    service = get_general_edu_service()
    
    for group_key in ['science', 'humanities', 'social', 'art']:
        courses = service.get_group_courses(group_key)
        print(f"  {group_key}: 加载了 {len(courses)} 门课程")
    
    all_courses = service.get_all_courses()
    print(f"  总计: {len(all_courses)} 门课程")
    
    # 2. 测试课程查询
    print("\n2. 测试课程查询")
    course = service.find_course_by_code("00240342")
    if course:
        print(f"  查找课程号 00240342: {course.name} ({course.group})")
    
    course = service.find_course_by_name("数据科学导论")
    if course:
        print(f"  查找'数据科学导论': {course.code} ({course.group})")
    
    # 3. 测试完成情况分析
    print("\n3. 测试完成情况分析")
    
    # 模拟已修课程
    completed_courses = [
        {"code": "00240342", "name": "数据科学导论", "credits": 2.0, "grade": "A-", "is_passed": True},
        {"code": "00240362", "name": "计算思维", "credits": 2.0, "grade": "B+", "is_passed": True},
        {"code": "00690622", "name": "中国古典诗歌研究与赏析", "credits": 2.0, "grade": "A", "is_passed": True},
        {"code": "00780051", "name": "舞蹈欣赏与实践", "credits": 1.0, "grade": "P", "is_passed": True},
        {"code": "00510133", "name": "会计学原理", "credits": 3.0, "grade": "B", "is_passed": True},
    ]
    
    result = analyze_general_edu_completion(completed_courses)
    
    print(f"  总学分要求: {result['total_required']}")
    print(f"  已修学分: {result['total_earned']}")
    print(f"  剩余学分: {result['total_missing']}")
    print(f"  所有课组完成: {result['all_groups_complete']}")
    
    print("\n  各课组完成情况:")
    for group in result['groups']:
        status = "[完成]" if group['is_complete'] else "[未完成]"
        print(f"    {status} {group['group_name']}: {group['credits_earned']}/{group['credits_required']} 学分")
    
    # 4. 测试缺口分析
    print("\n4. 测试缺口分析")
    gaps = analyze_general_edu_gaps(completed_courses)
    print(f"  未完成课组数: {len(gaps['incomplete_groups'])}")
    for g in gaps['incomplete_groups']:
        print(f"    - {g['group_name']}: 还差 {g['credits_missing']} 学分")
    
    # 5. 测试推荐功能
    print("\n5. 测试推荐功能")
    recommendations = recommend_general_edu_courses(
        completed_courses,
        user_preferences={"interests": ["人工智能", "数据"]}
    )
    print(f"  推荐课程数: {recommendations['total_count']}")
    for rec in recommendations['recommendations'][:5]:
        print(f"    - {rec['course_name']} ({rec['group_name']}, 评分: {rec['rating']:.1f})")
    
    # 6. 生成报告
    print("\n6. 生成分析报告")
    report = generate_general_edu_report(completed_courses)
    # 保存到文件
    output_file = Path(__file__).parent / "test_general_edu_output.md"
    output_file.write_text(report, encoding='utf-8')
    print(f"  报告已保存到: {output_file}")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    test_service()
