# 通识选修课课组功能说明

## 功能概述

本功能实现了对清华大学未央书院学生通识选修课（科学、人文、社科、艺术四大课组）的智能分析和管理。

## 文件结构

```
generalEdu/
├── science.md          # 科学课组课程列表（277门）
├── Humanities.md       # 人文课组课程列表（138门）
├── Social.md           # 社科课组课程列表（140门）
├── Art.md              # 艺术课组课程列表（202门）
└── README.md           # 本文件

backend/services/
├── general_edu_service.py          # 通识课核心服务
├── general_edu_recommendation.py   # 通识课推荐引擎
└── gap_calculator.py               # 集成通识课分析的缺口计算器

backend/agent/
├── general_edu_tools.py    # 通识课工具函数
└── chat_graph.py           # 集成通识课意图的对话状态图

backend/agent/chat_prompts.py  # 更新意图识别提示词
```

## 核心功能

### 1. 课组学分统计

根据学生成绩单，自动判断：
- 每个课组（科学/人文/社科/艺术）已修多少学分
- 是否满足各课组最低 2 学分的要求
- 通识选修课总学分（11学分）完成情况

### 2. 缺口分析

回答学生关于通识课的问题：
- "我哪个课组没修满？"
- "我还差几学分？"
- "我通识课完成情况如何？"

### 3. 智能推荐

结合课程评分数据（info_courses_stars/），推荐：
- 优先推荐未完成课组的课程
- 基于课程评分排序
- 支持按兴趣标签筛选

## 课组学分要求

根据培养方案：
- **总学分要求**: 11 学分
- **各课组最低要求**: 2 学分/课组
- **四大课组**: 科学、人文、社科、艺术

## API 使用示例

### 分析通识课完成情况

```python
from backend.services.general_edu_service import analyze_general_edu_completion

completed_courses = [
    {"code": "00240342", "name": "数据科学导论", "credits": 2.0, "is_passed": True},
    {"code": "00690622", "name": "中国古典诗歌研究与赏析", "credits": 2.0, "is_passed": True},
    # ... 更多课程
]

result = analyze_general_edu_completion(completed_courses)
print(f"总学分: {result['total_earned']}/{result['total_required']}")
print(f"所有课组完成: {result['all_groups_complete']}")

for group in result['groups']:
    print(f"{group['group_name']}: {group['credits_earned']}/{group['credits_required']} 学分")
```

### 推荐通识课

```python
from backend.services.general_edu_recommendation import recommend_general_edu_courses

result = recommend_general_edu_courses(
    completed_courses,
    user_preferences={"interests": ["人工智能", "历史"]}
)

for rec in result['recommendations']:
    print(f"{rec['course_name']} ({rec['group_name']}) - 评分: {rec['rating']}")
```

### 获取缺口描述

```python
from backend.agent.general_edu_tools import get_general_education_gaps

report = get_general_education_gaps(completed_courses)
print(report)
```

## 对话场景示例

### 场景 1: 查询通识课完成情况

**用户**: "我通识课修得怎么样了？"

**助手**: 
```
**通识选修课完成情况**

总体进度: 9/11 学分 (81.8%)

✅ 科学课组: 4/2 学分
✅ 人文课组: 2/2 学分  
✅ 社科课组: 3/2 学分
⚠️ 艺术课组: 0/2 学分

您有 1 个课组未完成最低学分要求，建议优先补足。
**艺术课组**还需修读 2.0 学分
```

### 场景 2: 推荐通识课

**用户**: "给我推荐一些通识课，我对人工智能感兴趣"

**助手**: 基于缺口分析，优先推荐艺术课组的高评分课程，同时筛选包含"人工智能"相关内容的课程。

### 场景 3: 询问具体课组

**用户**: "我艺术课组还差多少学分？"

**助手**: "您目前艺术课组修了 1.0 学分，还差 1.0 学分。建议选修：建筑与城市美学 (1学分)、中国近代建筑风格辨析与鉴赏 (1学分) 等课程。"

## 数据说明

### 课程数据来源
- 课程列表: generalEdu/ 目录下的 markdown 文件
- 课程评分: info_courses_stars/ 目录下的评教数据
- 课组要求: 2023级培养方案（通识选修课 11 学分，每课组至少 2 学分）

### 课程匹配逻辑
- 优先匹配课程号
- 支持课程名模糊匹配
- 自动处理重复课程（取最高成绩）

## 集成说明

本功能已集成到多轮对话系统中：

1. **意图识别**: LLM 自动识别通识课相关查询（关键词：通识课、课组、还差几学分等）
2. **节点处理**: `general_edu_node` 统一处理通识课分析和推荐
3. **响应生成**: 根据用户具体提问生成个性化回复

## 测试

运行测试脚本：

```bash
python scripts/test_general_edu.py
```

测试输出保存在 `scripts/test_general_edu_output.md`
