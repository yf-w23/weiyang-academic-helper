# 智能选课助手系统 (Smart Course Advisor) - Prototype Design

**版本**: v0.1   

**状态**: 概念验证阶段

---



## 1. 项目概述

### 1.1 问题定义

大学选课场景中存在以下痛点：

- **信息过载**：数千门课程、多维度分类（院系/通识/模块）、海量历史评价
- **约束复杂**：培养方案硬性要求（学分/先修课/模块）、时间冲突、容量限制
- **需求模糊**：学生常使用自然语言提问（如"给分好的数理基础课"），难以映射到结构化查询
- **个性化冲突**：需平衡"毕业紧迫性"与"课程质量偏好"

### 1.2 核心目标

构建一个**混合架构的Agent系统**，能够：

1. 理解自然语言查询意图（LLM层）
2. 精确执行培养方案约束检查（硬编码层）
3. 基于历史评分数据生成个性化推荐（数据引擎层）
4. 提供可解释的选课建议（LLM增强层）

---



## 2. 系统架构

### 2.1 分层架构图

```



┌─────────────────────────────────────────────────────────────────┐

│                    交互层 (Interface Layer)                        │

│  • 自然语言对话接口                                               │

│  • 培养方案上传解析                                               │

│  • 课表可视化展示                                                 │

└──────────────────────┬──────────────────────────────────────────┘

│

┌──────────────────────▼──────────────────────────────────────────┐

│                    意图层 (Intent Layer) - LLM驱动               │

│  • Query Router: 将用户查询分类为实体查询/聚合统计/语义探索/复杂推理 │

│  • 查询改写: "张三的课" → {teacher: "张三"}                       │

│  • 培养方案文本解析: PDF/Word → 结构化规则                         │

└──────────────────────┬──────────────────────────────────────────┘

│

┌──────────────────────▼──────────────────────────────────────────┐

│                    引擎层 (Engine Layer) - 硬编码核心              │

│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐  │

│  │  约束引擎        │  │  推荐引擎        │  │  评分聚合引擎     │  │

│  │  • 缺口计算      │  │  • 候选集生成    │  │  • 历史数据挖掘   │  │

│  │  • 先修课检查    │  │  • 多目标排序    │  │  • 情感分析      │  │

│  │  • 冲突检测      │  │  • 课表优化(ILP) │  │  • 教师维度区分   │  │

│  └─────────────────┘  └─────────────────┘  └──────────────────┘  │

└──────────────────────┬──────────────────────────────────────────┘

│

┌──────────────────────▼──────────────────────────────────────────┐

│                    存储层 (Storage Layer) - 混合数据库            │

│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │

│  │ PostgreSQL   │  │  Milvus/     │  │ Neo4j                   │ │

│  │ (关系型)      │  │  pgvector    │  │ (图数据库)              │ │

│  │ • 课程元数据  │  │ (向量)        │  │ • 培养方案DAG           │ │

│  │ • 用户进度    │  │ • 语义搜索    │  │ • 先修课依赖            │ │

│  │ • 评分聚合    │  │ • 相似度计算  │  │ • 教师-课程关系         │ │

│  └──────────────┘  └──────────────┘  └──────────────────────────┘ │

└───────────────────────────────────────────────────────────────────┘



```

### 2.2 职责边界划分


| 模块类型      | 实现方式              | 典型任务                    | 性能要求        |
| --------- | ----------------- | ----------------------- | ----------- |
| **硬编码**   | Python/SQL/Cypher | 学分计算、先修课检查、时间冲突检测、ILP优化 | P99 < 50ms  |
| **LLM增强** | GPT-4/Claude/Kimi | 意图识别、查询改写、推荐理由生成、评价情感分析 | P95 < 2s    |
| **混合协作**  | LLM作为重排序器         | 在硬编码Top50候选基础上进行语义精排    | P95 < 500ms |


---



## 3. 数据模型设计

### 3.1 关系型模型 (PostgreSQL)

**核心实体表**

```sql

-- 课程基础信息

CREATE TABLE courses (

    course_id VARCHAR(20) PRIMARY KEY,

    code VARCHAR(20),

    title VARCHAR(200),

    credits INT,

    department VARCHAR(50),

    category VARCHAR(50),        -- 专业必修/专业选修/通识/数理基础

    description TEXT,

    workload_hours INT,           -- 每周学时

    tags TEXT[]                 -- GIN索引支持的多标签

);



-- 开课实例（区分学期和教师）

CREATE TABLE course_offerings (

    offering_id VARCHAR(20) PRIMARY KEY,

    course_id VARCHAR(20),

    teacher_id VARCHAR(20),

    semester VARCHAR(20),        -- 2024-Spring

    schedule_slots JSONB,        -- [{day: "Mon", start: "08:00", end: "09:35"}]

    capacity INT,

    location VARCHAR(50),

    FOREIGN KEY (course_id) REFERENCES courses(course_id)

);



-- 用户完成进度（与培养方案绑定）

CREATE TABLE user_progress (

    user_id VARCHAR(20),

    program_id VARCHAR(20),

    group_id VARCHAR(20),        -- 培养方案模块ID

    required_credits INT,

    completed_credits INT DEFAULT 0,

    completed_courses TEXT[],    -- PostgreSQL数组

    in_progress_courses TEXT[],

    PRIMARY KEY (user_id, group_id)

);



-- 评分聚合（物化视图，每小时刷新）

CREATE MATERIALIZED VIEW course_rating_stats AS

SELECT 

    co.course_id,

    co.teacher_id,

    AVG(r.quality_score) as avg_quality,

    AVG(r.difficulty_score) as avg_difficulty,

    COUNT(r.review_id) as review_count,

    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY r.quality_score) as median_quality

FROM course_offerings co

LEFT JOIN reviews r ON co.offering_id = r.offering_id

GROUP BY co.course_id, co.teacher_id;

```

### 3.2 向量模型 (Milvus/pgvector)

```python

# 课程复合向量表示

course_vectors = [

    {

        "course_id": "CS202",

        "description_vector": [...],      # 课程描述Embedding (bge-m3)

        "syllabus_vector": [...],          # 教学大纲Embedding

        "reviews_summary_vector": [...],   # 评价摘要Embedding（捕捉"硬核"、"水课"等）

        "prerequisites_vector": [...],     # 能力要求Embedding

        "metadata": {

            "department": "计算机系",

            "category": "专业核心",

            "avg_quality": 4.6

        }

    }

]

```

### 3.3 图模型 (Neo4j)

```cypher

// 培养方案规则图

(:Program {name: "CS-2022"})-[:HAS_GROUP]->(:ReqGroup {name: "专业核心", min_credits: 20})

(:ReqGroup)-[:ALLOWS]->(:Category {code: "CS_CORE"})

(:Course {code: "CS202"})-[:BELONGS_TO]->(:Category {code: "CS_CORE"})



// 课程依赖链

(:Course {code: "CS202"})-[:PREREQUISITE {strict: true, type: "hard"}]->(:Course {code: "CS101"})

(:Course {code: "CS301"})-[:PREREQUISITE {strict: false, type: "recommended"}]->(:Course {code: "MATH201"})



// 互斥关系（替代课程）

(:Course {code: "CS102"})-[:MUTUALLY_EXCLUSIVE {reason: "content_overlap"}]->(:Course {code: "EE105"})



// 评价关系

(:Student)-[:RATED {quality: 5, difficulty: 4, semester: "2024S"}]->(:CourseOffering)

(:CourseOffering)-[:INSTANCE_OF]->(:Course)

```

---



## 4. 核心算法流程

### 4.1 约束满足引擎 (Constraint Engine)

**缺口计算算法 (Gap Analysis)**

```python

class CurriculumEngine:

    def calculate_gaps(self, user_id: str) -> List[RequirementGap]:

        """

        识别用户为满足培养方案而必须填补的缺口

        """

        # 1. 获取用户已完成课程

        completed = self.get_completed_courses(user_id)

        

        # 2. 获取培养方案要求（图遍历）

        program_rules = self.graph.get_program_structure(user_id)

        

        gaps = []

        for group in program_rules.requirement_groups:

            # 学分缺口计算

            if group.type == "credit_based":

                earned = sum(c.credits for c in completed if c.category in group.allowed_categories)

                if earned < group.min_credits:

                    gaps.append(CreditGap(

                        group_id=group.id,

                        remaining=group.min_credits - earned,

                        allowed_categories=group.allowed_categories

                    ))

            

            # 特定课程缺口（如必修缺哪几门）

            elif group.type == "course_based":

                missing = set(group.required_courses) - set(c.id for c in completed)

                if missing:

                    gaps.append(CourseGap(group_id=group.id, required_courses=missing))

        

        return gaps

```

**先修课验证 (Prerequisite Check)**

```python

def check_prerequisites(course_id: str, completed_courses: Set[str], graph) -> Tuple[bool, List[str]]:

    """

    使用图遍历检查所有先修课是否满足（支持软先修/硬先修）

    """

    query = """

    MATCH path = (c:Course {id: $course_id})-[:PREREQUISITE*1..10]->(p:Course)

    RETURN p.id as prereq_id, r.type as req_type

    """

    prerequisites = graph.run(query, course_id=course_id).data()

    

    violations = []

    for prereq in prerequisites:

        if prereq['req_type'] == 'hard' and prereq['prereq_id'] not in completed_courses:

            violations.append(prereq['prereq_id'])

    

    return len(violations) == 0, violations

```

### 4.2 推荐引擎 (Recommendation Engine)

**两阶段过滤 + 多目标排序**

```python

class CourseRecommender:

    def recommend(self, user_id: str, query_intent: Dict, top_k: int = 10) -> List[Recommendation]:

        # Phase 1: 硬约束过滤（从1000+门课筛选到~100门候选）

        candidates = self.hard_filter(user_id)

        # 过滤条件：

        # - 满足缺口要求（这门课能计入某未完成模块）

        # - 先修课已满足

        # - 时间冲突排除

        # - 容量未满

        

        if not candidates:

            return []  # 触发"冲突消解对话"（LLM介入）

        

        # Phase 2: 多目标评分（候选集内精排）

        scored = []

        for course in candidates:

            score = self.multi_objective_score(course, user_id)

            scored.append((course, score))

        

        # Phase 3: 多样化重排序（避免全推同一时间段/同一老师）

        diversified = self.diversify_results(scored, top_k)

        

        return diversified

    

    def multi_objective_score(self, course: Course, user_id: str) -> float:

        """

        加权评分公式（硬编码，可解释）

        """

        # 1. 约束满足度 (40%)

        gap_fitness = self.calculate_gap_fitness(course, user_id)  # 填补缺口能力

        unlock_potential = self.calculate_unlock_potential(course, user_id)  # 解锁后续课程数

        

        # 2. 课程质量 (35%)

        quality = course.avg_quality / 5.0  # 归一化

        difficulty_match = 1 - abs(course.avg_difficulty - self.user_ability[user_id]) / 4.0

        

        # 3. 个性化 (25%)

        content_sim = self.vector_similarity(course, self.user_preference_vector[user_id])

        

        # 加权总和

        return (

            0.25 * gap_fitness + 

            0.15 * unlock_potential + 

            0.25 * quality + 

            0.10 * difficulty_match + 

            0.25 * content_sim

        )

```

**学期级课表优化 (ILP Solver)**

```python

def optimize_schedule(self, user_id: str, gaps: List[Gap]) -> List[Course]:

    """

    使用整数线性规划求解最优学期课表

    目标：在满足所有缺口的前提下，最大化总评分且平衡工作量

    """

    prob = LpProblem("Semester_Schedule", LpMaximize)

    

    # 决策变量：是否选这门课

    course_vars = {c.id: LpVariable(f"x_{c.id}", cat='Binary') 

                   for c in self.available_courses}

    

    # 目标函数：最大化推荐分数 - 工作量惩罚（防止全选硬核课）

    prob += lpSum([course_vars[c.id] * c.score for c in self.available_courses]) - \

            0.05 * lpSum([course_vars[c.id] * c.workload for c in self.available_courses])

    

    # 约束1：必须满足所有学分缺口

    for gap in gaps:

        if isinstance(gap, CreditGap):

            prob += lpSum([

                course_vars[c.id] * c.credits 

                for c in self.available_courses 

                if c.category in gap.allowed_categories

            ]) >= gap.remaining_credits

    

    # 约束2：总学分不超过学期上限（如25学分）

    prob += lpSum([course_vars[c.id] * c.credits for c in self.available_courses]) <= 25

    

    # 约束3：时间冲突（预计算冲突矩阵）

    for c1, c2 in self.time_conflicts:

        prob += course_vars[c1.id] + course_vars[c2.id] <= 1

    

    prob.solve()

    return [c for c in self.available_courses if course_vars[c.id].value() == 1]

```

### 4.3 LLM增强层 (LLM Augmentation)

**查询路由 (Query Router)**

```python

class QueryRouter:

    def route(self, user_query: str) -> RetrievalStrategy:

        """

        使用轻量级LLM分类查询类型，决定检索路径

        """

        prompt = f"""

        分析学生查询意图，返回JSON格式：

        查询: "{user_query}"

        

        分类：

        - entity_lookup: 实体查询（特定老师/课号）-> 图数据库精确匹配

        - aggregate: 聚合统计（"平均分如何"）-> SQL聚合查询

        - semantic: 语义探索（"适合文科生的编程课"）-> 向量检索+重排序

        - complex: 复杂推理（"没学高数能选ML吗"）-> 图+LLM混合推理

        """

        result = llm.generate_json(prompt, temperature=0.0)

        return RetrievalStrategy(result['classification'])

```

**推荐理由生成 (Explanation Generation)**

```python

def generate_explanation(self, recommendation: Recommendation, user_id: str) -> str:

    """

    基于硬编码计算出的结构化数据，生成自然语言解释

    """

    context = {

        "course_name": recommendation.course.title,

        "teacher": recommendation.course.teacher_name,

        "quality_score": recommendation.course.avg_quality,

        "gap_filled": recommendation.gap_filled,  # 填补哪个模块缺口

        "prerequisites_met": recommendation.prereqs_met,

        "difficulty": recommendation.course.avg_difficulty,

        "user_profile": self.get_user_summary(user_id)

    }

    

    prompt = f"""

    基于以下结构化数据，为学生生成个性化选课建议（2-3句话）：

    {json.dumps(context, ensure_ascii=False)}

    

    要求：

    1. 说明这门课为什么适合该学生（结合其培养方案缺口和历史偏好）

    2. 提及课程评分数据（如"往届学生评分4.8/5"）

    3. 如有先修课要求，确认其已满足

    4. 语气友好、专业，避免过度承诺

    

    示例输出：

    "这门《数据结构》能帮你补齐专业核心模块的6学分缺口。授课老师张老师评分4.8分，\

    学生评价'项目实战多'，与你偏好的实践类课程匹配。你已修完先修课《C语言》，可以顺利选修。"

    """

    return llm.generate(prompt, temperature=0.7)

```

---



## 5. API 接口设计

### 5.1 核心API端点

```yaml

# 查询培养方案缺口

GET /api/v1/users/{user_id}/gaps

Response:

{

  "gaps": [

    {

      "group": "专业选修",

      "type": "credits",

      "required": 6,

      "completed": 2,

      "remaining": 4,

      "deadline": "2026-06-30"

    }

  ]

}



# 获取推荐（核心接口）

POST /api/v1/recommendations

Body:

{

  "user_id": "U2022001",

  "query": "我想选一门给分好的数理基础课",

  "constraints": {

    "exclude_time_slots": ["Mon 08:00-09:35"],

    "max_difficulty": 4.0

  }

}

Response:

{

  "recommendations": [

    {

      "course": {

        "id": "MATH201",

        "title": "线性代数",

        "teacher": "李四",

        "credits": 4,

        "schedule": "Wed 14:00-15:35"

      },

      "score": 0.92,

      "reasoning": {

        "gap_fitness": 0.67,      # 填补4学分中的4学分

        "quality_score": 4.7,

        "difficulty_match": 0.85,

        "explanation": "这门课能帮你补齐数理基础模块剩余的4学分缺口..."

      }

    }

  ],

  "query_intent": {

    "type": "semantic",

    "extracted_constraints": {"category": "数理基础", "quality_focus": true}

  }

}



# 检查选课方案可行性

POST /api/v1/schedule/validate

Body:

{

  "user_id": "U2022001",

  "proposed_courses": ["CS202", "MATH201", "PHY101"]

}

Response:

{

  "valid": false,

  "violations": [

    {

      "type": "time_conflict",

      "courses": ["CS202", "PHY101"],

      "conflict_slots": ["Fri 10:00-11:35"]

    },

    {

      "type": "prerequisite_missing",

      "course": "CS202",

      "missing_prereq": "CS101"

    }

  ],

  "alternatives": [

    {

      "original": "PHY101",

      "suggestion": "PHY102（同时间段周三班，内容相同）"

    }

  ]

}

```

---



## 6. 技术栈选型


| 组件     | 推荐方案                    | 备选方案                  | 选型理由                           |
| ------ | ----------------------- | --------------------- | ------------------------------ |
| 主数据库   | PostgreSQL + pgvector   | MySQL + 独立向量库         | JSONB 支持灵活标签，pgvector 支持向量联合查询 |
| 图数据库   | Neo4j                   | Dgraph                | Cypher 查询直观，社区成熟，支持复杂路径查询      |
| 向量检索   | pgvector (IVFFlat/HNSW) | Milvus, Pinecone      | 减少技术栈复杂度，同一数据库内完成混合查询          |
| LLM    | GPT-4o (复杂推理)           | Claude 3.5, Kimi K2.5 | JSON mode 可靠，适合意图识别            |
| 轻量 LLM | Local Mistral-7B        | Phi-3, Gemma-2B       | 本地部署用于简单分类，降低 API 成本           |
| 优化求解   | PuLP (Python)           | Google OR-Tools       | 轻量级 ILP 求解，足够处理学期课表优化          |
| 缓存层    | Redis                   | Memcached             | 缓存热门课程评分和 LLM 生成解释             |
| API 框架 | FastAPI                 | Flask, Go             | 异步支持，OpenAPI 自动生成              |


---



## 7. 实施路线图 (MVP → Production)

### Phase 1: 数据基础 (Week 1-2)

- 设计并实现PostgreSQL schema（课程、用户、评分表）
- 导入历史课程数据（至少2个学期的完整数据）
- 构建培养方案图模型（至少1个专业的完整规则）
- 实现基础CRUD API

### Phase 2: 约束引擎 (Week 3-4)

- 实现缺口计算算法（Gap Analysis）
- 实现先修课检查（图遍历）
- 实现时间冲突检测
- 构建验证API（检查课表可行性）

### Phase 3: 推荐核心 (Week 5-6)

- 实现硬约束过滤（SQL层面）
- 实现多目标评分公式
- 集成ILP求解器进行学期优化
- 集成向量数据库（课程描述Embedding）

### Phase 4: LLM增强 (Week 7-8)

- 实现查询路由（Query Router）
- 实现查询改写（自然语言→结构化）
- 实现推荐理由生成（基于硬编码结果）
- 实现评价情感分析（离线批处理）

### Phase 5: 集成与优化 (Week 9-10)

- 端到端Agent流程集成
- 添加缓存层（Redis）
- 压力测试（目标：100并发下推荐延迟<2s）
- 异常处理（无满足方案时的协商对话）

---



## 8. 关键设计决策 (ADR)

### ADR-001: 混合数据库架构

**决策**: 采用 PostgreSQL (关系型) + Neo4j (图) + pgvector (向量) 而非单一数据库

**理由**:

- 培养方案约束需要图遍历（Neo4j最擅长）
- 评分聚合需要复杂SQL窗口函数（PostgreSQL最擅长）
- 语义搜索需要向量相似度（pgvector避免数据同步延迟）

### ADR-002: 约束满足优先于评分优化

**决策**: 推荐算法第一阶段必须过滤掉不满足培养方案的课程，第二阶段才考虑评分

**理由**:

- 毕业资格是硬性约束，不能妥协
- 减少LLM需要考虑的候选集规模（1000→50），降低成本

### ADR-003: LLM 仅用于“解释”而非“决策”

**决策**: 课程是否可选、评分计算、时间冲突检测必须由硬编码完成，LLM 仅用于生成解释文本和意图理解

**理由**:

- 数学计算和逻辑判断的确定性要求（不能出现"可能满足先修课"）
- 成本考虑：硬编码查询成本为0，LLM调用成本较高
- 可测试性：硬编码逻辑可以单元测试，LLM输出难以精确测试

### ADR-004: 预计算 vs 实时计算

**决策**:

- 课程评分聚合、评价情感分析 → 预计算（每小时物化视图刷新）
- 用户缺口计算、课表冲突检测 → 实时计算（数据更新频繁）
- 向量Embedding → 预计算（课程内容不常变，但查询时做ANN检索）

---



## 9. 风险评估与缓解


| 风险         | 影响  | 缓解策略                                              |
| ---------- | --- | ------------------------------------------------- |
| LLM 意图识别错误 | 高   | 添加置信度阈值，低置信度时回退到关键词匹配；提供用户确认机制                    |
| 培养方案规则变更   | 高   | 版本控制：`program_id` 包含版本号（如 `CS-2022-v3`）；历史用户绑定旧版本 |
| 课程无历史评分    | 中   | 冷启动策略：新课使用教师历史评分均值；相似课程评分加权                       |
| 性能瓶颈（向量检索） | 中   | HNSW 索引；结果缓存；相似查询合并                               |
| 数据隐私（学生成绩） | 高   | 数据脱敏：LLM 层不接触真实成绩，仅接触分类后的“能力等级”；API 权限控制          |


---



## 10. 成功指标 (KPI)

### 1. 准确性指标

- 推荐课程的先修课满足率：>99%
- 培养方案缺口填补成功率：>95%
- 时间冲突检测准确率：100%

### 2. 用户体验指标

- 端到端响应时间（查询→推荐）：< 2秒
- 推荐接受率（学生实际选择推荐课程的比例）：> 40%
- 自然语言查询理解准确率（人工抽检）：> 85%

### 3. 系统健康指标

- API可用性：> 99.5%
- LLM调用成本/查询：<0.02（通过缓存和轻量模型降低）

---



## 附录：示例交互流程

**场景**: 学生问“我下学期该选什么课才能按时毕业，想要给分好的”

**系统内部流程**:

1. 意图层 (LLM): 识别为`gap_filling` + `quality_preference`，提取时间范围"下学期"
2. 引擎层 (硬编码):
  - 查询用户缺口：发现专业选修差6学分，且必修CS202未修
  - 过滤候选：先修课检查排除CS301（因CS202未修），时间冲突排除周五早八课程
  - 生成候选集：CS202（必修，4分）、CS205（选修，3分）、CS210（选修，3分）
  - 评分计算：CS202（0.95分，缺口填补1.0 + 质量0.8）、CS205（0.88分）、CS210（0.82分）
  - ILP优化：推荐组合[CS202, CS205]（总学分7，满足缺口）
3. 接口层 (LLM): 生成解释："推荐您下学期选修《数据结构》(CS202)和《数据库原理》(CS205)。前者是专业必修且为您解锁6门高阶课，张老师授课评分4.6分；后者可填补选修学分缺口，学生评价'给分 generous'..."

---

**文档维护**: 本 Prototype 应随技术选型和业务需求变更迭代，每次重大架构决策需更新 ADR 章节。