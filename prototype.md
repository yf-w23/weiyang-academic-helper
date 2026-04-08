# 未央书院选课助手智能体 — 原型设计文档

## 一、项目概述

面向未央书院学生的智能学业规划助手。用户通过**多轮对话**完成以下流程：上传成绩单 PDF → 自动解析并对比培养方案 → 生成缺口分析报告 → 交互式选课推荐 → 课程详情查询。整体体验类似于网页版 DeepSeek 的对话式交互。

### 核心功能

| # | 功能 | 描述 | 当前状态 |
|---|------|------|---------|
| F1 | 培养方案缺口分析 | 上传成绩单 PDF，系统自动识别年级班级，OCR 提取后对比培养方案，生成缺口报告 | 已实现（单轮 API + 自动信息识别），待升级为结构化分析 |
| F2 | 多轮对话式交互 | 将 F1 及后续功能整合到统一聊天界面，支持流式输出 | 待开发 |
| F3 | 智能选课推荐 | 基于缺口分析 + 先修链分析 + 用户偏好，推荐下学期可选课程 | 待开发 |
| F4 | 课程信息查询 | 查询课程的开课学期、考试形式、作业要求等 | 待开发（需数据源） |
| F5 | PDF 缓存 | 对已解析过的 PDF（MD5 匹配）跳过 OCR，直接返回缓存结果 | 待开发 |

### 技术创新点（答辩亮点）

以下是本项目与同类竞品的核心差异，也是其他团队短期内难以复制的壁垒：

| 创新点 | 别人的做法 | 我们的做法 | 为什么别人难做 |
|--------|-----------|-----------|--------------|
| **结构化精确分析** | 把文本整段丢给 LLM，让 LLM "算"学分差，结果不可验证 | 培养方案和成绩单先解析为结构化数据（课程树 / 课程列表），**代码层面精确计算学分**，LLM 只负责生成自然语言报告 | 需要针对培养方案 Markdown 格式写专门的解析器，针对 OCR 输出的成绩单格式写结构化提取逻辑，这属于脏活累活 |
| **先修链拓扑排序** | 推荐只看"你缺什么课"，不考虑课程之间的依赖关系 | 构建课程先修依赖图，计算每门课的"阻塞系数"（不修它会导致多少后续课无法选修），据此排优先级 | 需要手动收集并维护先修关系数据，需要实现图算法 |
| **课程知识图谱数据** | 最多做到查课表信息 | 积累了一份结构化的课程详情数据（开课学期、考核方式、工作量、先修关系），覆盖核心课程 | 数据收集本身是时间壁垒，别人短期内无法获得同等规模的结构化课程数据 |

---

## 二、目标项目结构

```text
Agent_competition/
├── README.md
├── .env.example
├── .gitignore
├── pyproject.toml
├── prototype.md                    # 本文件
│
├── backend/
│   ├── __init__.py
│   ├── main.py                     # FastAPI 入口，挂载路由与中间件
│   ├── config.py                   # pydantic-settings 配置管理
│   │
│   ├── api/                        # API 路由层
│   │   ├── __init__.py
│   │   ├── deps.py                 # 依赖注入
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py           # GET /health
│   │       ├── advise.py           # POST /api/advise/gap-analysis（保留单轮接口）
│   │       └── chat.py             # [F2] POST /api/chat — 对话式交互入口（SSE 流式）
│   │
│   ├── agent/                      # LangGraph 智能体编排
│   │   ├── __init__.py
│   │   ├── graph.py                # 状态图：extract_transcript → load_schema → analyze_gap
│   │   ├── chat_graph.py           # [F2] 多轮对话状态图（含意图路由）
│   │   ├── runner.py               # 单轮分析入口（供 advise 路由调用）
│   │   ├── tools.py                # Agent 可调用工具（OCR、方案加载、课程查询等）
│   │   └── prompts.py              # 系统提示词与模板
│   │
│   ├── services/                   # 业务逻辑（不依赖 HTTP，便于单测）
│   │   ├── __init__.py
│   │   ├── graduation.py           # 培养方案加载 + 结构化解析（Markdown → 课程树）
│   │   ├── transcript_parser.py    # 【创新】成绩单结构化解析（OCR 文本 → 课程列表）
│   │   ├── gap_calculator.py       # 【创新】精确缺口计算（代码计算学分，非 LLM 估算）
│   │   ├── prerequisite_graph.py   # 【创新】先修链分析与拓扑排序
│   │   ├── ocr_service.py          # OCR 云端服务（PaddleOCR API，自动回退本地）
│   │   ├── ocr_service_local.py    # 本地 OCR（PaddleOCR + pdf2image）
│   │   ├── llm_service.py          # DeepSeek API 封装（OpenAI 兼容，支持流式）
│   │   ├── cache_service.py        # [F5] PDF MD5 缓存服务
│   │   ├── course_info.py          # [F4] 课程信息查询服务
│   │   └── recommendation.py       # [F3] 选课推荐（结合先修链优先级 + 用户偏好）
│   │
│   ├── schemas/                    # Pydantic 请求/响应模型
│   │   ├── __init__.py
│   │   └── advise.py
│   │
│   ├── data/                       # 结构化数据文件
│   │   ├── DegreeRequirements/     # 培养方案 Markdown（2021-2025 级）
│   │   │   ├── 2021未央书院培养方案.md
│   │   │   ├── 2022未央书院培养方案.md
│   │   │   ├── 2023未央书院培养方案.md
│   │   │   ├── 2024未央书院培养方案.md
│   │   │   └── 2025未央书院培养方案.md
│   │   └── courses/                # [F3/F4] 课程信息数据（JSON）
│   │       ├── course_schedule.json    # 开课学期、学分、课组归属
│   │       ├── prerequisites.json     # 【创新】课程先修关系（构建依赖图的输入）
│   │       └── course_details.json     # 考核方式、作业要求等（逐步补充）
│   │
│   ├── cache/                      # [F5] OCR 结果缓存目录
│   │   └── {md5hash}.md
│   │
│   ├── paddleocr_doc_parsing/      # PaddleOCR 文档解析库
│   └── utils/
│       └── file_utils.py           # 文件工具函数
│
├── frontend/
│   ├── react-app/                  # React 前端（主力，需改造为聊天界面）
│   │   ├── package.json
│   │   └── src/
│   │       ├── App.tsx
│   │       ├── components/
│   │       │   ├── Layout.tsx          # 页面主布局
│   │       │   ├── Hero.tsx            # 首页 Hero 区域
│   │       │   ├── UploadForm.tsx      # 成绩单上传表单（自动识别年级班级）
│   │       │   ├── ResultDisplay.tsx   # 分析结果展示
│   │       │   └── ...
│   │       ├── pages/
│   │       │   └── ChatPage.tsx        # [F2] 对话页面（替代原 HomePage）
│   │       ├── api/
│   │       │   └── client.ts           # 后端 API 客户端（含 SSE 流式解析）
│   │       └── types/
│   │           └── index.ts
│   └── streamlit_app/              # Streamlit 前端（备选，功能同步）
│       ├── app.py
│       ├── config.py
│       └── api_client.py
│
├── scripts/
│   ├── test_ocr.py
│   └── test_ocr_api.py
│
└── tests/                          # 单元测试
    ├── conftest.py
    ├── test_graduation_service.py
    ├── test_cache_service.py
    └── test_agent_tools.py
```

---

## 三、功能详细设计

### F1 — 培养方案缺口分析

#### 当前实现

单轮 API 模式：`POST /api/advise/gap-analysis`，上传成绩单 PDF 后，系统先通过 OCR 提取文本并自动识别入学年份和班级，然后 LangGraph 状态图依次执行 `extract_transcript → load_schema → analyze_gap`，由 LLM 直接对比分析。**保留此接口**，同时作为 F2 多轮对话中的后端能力被内部调用。

#### 升级方向：结构化精确分析（技术创新）

当前 LLM 直接对比原始文本，学分计算完全依赖 LLM 的"理解"，结果不可验证、不可复现。升级为**结构化解析 + 代码精确计算 + LLM 仅生成报告**的三段式流程：

```
                    当前做法                              升级后做法
            ┌─────────────────┐                ┌─────────────────────────┐
            │ OCR 文本（整段） │                │ OCR 文本（整段）         │
            │       +         │                │       +                 │
            │ 培养方案（整段） │                │ 培养方案（整段）         │
            │       ↓         │                │       ↓                 │
            │  全部丢给 LLM   │       →        │  [结构化解析]            │
            │  LLM 自己算学分 │                │  成绩单 → 课程列表       │
            │  LLM 自己找缺口 │                │  培养方案 → 课程树       │
            │       ↓         │                │       ↓                 │
            │  返回分析报告    │                │  [代码精确计算]          │
            └─────────────────┘                │  学分差、完成率、缺课    │
                                               │       ↓                 │
                                               │  [LLM 生成报告]         │
                                               │  输入：结构化数据        │
                                               │  输出：自然语言报告      │
                                               └─────────────────────────┘
```

**关键模块拆分：**

**1) `services/graduation.py` — 培养方案结构化解析**

将培养方案 Markdown 解析为结构化课程树：

```python
# 解析结果数据结构示例
{
    "year": "2023",
    "total_credits_required": 170,
    "groups": [
        {
            "group_name": "通识教育",
            "credits_required": 40,
            "sub_groups": [
                {
                    "group_name": "通识基础课",
                    "credits_required": 20,
                    "courses": [
                        {"code": "10720111", "name": "线性代数(1)", "credits": 4, "required": True},
                        ...
                    ]
                }
            ]
        },
        {
            "group_name": "专业核心课",
            "credits_required": 50,
            "courses": [...]
        }
    ]
}
```

解析策略：针对培养方案 Markdown 的格式特征（标题层级、表格结构、学分标注），编写正则 + 规则解析器。不同年份的培养方案格式可能不同，需要逐年级适配或编写通用规则。

**2) `services/transcript_parser.py` — 成绩单结构化解析**

将 OCR 输出的成绩单文本解析为已修课程列表：

```python
# 解析结果数据结构示例
[
    {"code": "10720111", "name": "线性代数(1)", "credits": 4, "grade": "A-", "semester": "2023秋"},
    {"code": "40130343", "name": "数据结构", "credits": 3, "grade": "B+", "semester": "2024春"},
    ...
]
```

解析策略：OCR 输出的成绩单通常是表格格式（课程号 | 课程名 | 学分 | 成绩 | 学期），按行解析。需处理 OCR 识别错误（如把 "A-" 识别成 "A -"）。

此外，`transcript_parser.py` 还负责**自动提取学生的年级和班级信息**（如从 `2023年08月入学` 提取年份，从 `未央-电31` 提取班级），使用正则匹配成绩单中的固定字段，无需用户手动输入。

**3) `services/gap_calculator.py` — 精确缺口计算**

输入结构化的课程树 + 已修课程列表，输出精确的缺口分析：

```python
# 输出示例
{
    "total_credits_required": 170,
    "total_credits_earned": 142,
    "completion_rate": 0.835,           # 精确到小数的完成率
    "group_gaps": [
        {
            "group_name": "通识基础课",
            "credits_required": 20,
            "credits_earned": 18,
            "missing_courses": [
                {"code": "...", "name": "思政课xx", "credits": 2}
            ]
        },
        ...
    ],
    "missing_required": [...],          # 未修的必修课
    "elective_deficit": 4,              # 选修课还差多少学分
}
```

全部由 Python 代码计算（集合运算、学分累加），不经过 LLM，结果确定性、可单测。

**4) LLM 的角色变化**

LLM 不再负责"算"学分，改为：
- 接收 `gap_calculator.py` 输出的结构化缺口数据
- 结合用户的具体情况（班级、年级）生成自然语言的分析报告
- 给出选课建议和学习规划

**这样做的好处（答辩话术）：**

> "我们的缺口分析是确定性的——同一份成绩单分析两次结果完全一致。学分计算、课组匹配全部由代码完成，LLM 只负责把结构化数据翻译成用户看得懂的报告。这意味着分析结果是可验证、可复现的，不会因为 LLM 的随机性而产生不同的结论。"

---

### F2 — 多轮对话式交互

#### 交互设计

用户看到的界面类似网页版 DeepSeek：左侧对话历史列表，右侧当前对话的消息流。

**典型对话流程：**

```
用户：[上传 成绩单.pdf] 帮我分析一下我的培养方案完成情况

助手：成绩单上传成功！我已自动识别您为未央-电31（2023级）。
      [流式输出] 培养方案缺口分析报告（Markdown 渲染）
      ---
      你目前缺少以下课程：...
      你是否需要我帮你推荐下学期的选课？

用户：需要的，我比较喜欢软件类课程

助手：根据你的缺口和偏好，我推荐以下课程：
      1. xxx — 秋季开课，3学分...
      2. yyy — 春季开课，2学分...

用户：xxx 这门课考试多吗？有没有大作业？

助手：xxx 这门课：
      - 开课学期：秋季
      - 考核方式：期中 + 期末考试
      - 大作业：有（团队项目 + Presentation）
      ...
```

#### 技术方案

| 层 | 方案 |
|----|------|
| **后端 API** | 新增 `POST /api/chat`，接收 `{ session_id, message }`，成绩单通过 `POST /api/chat/upload` 上传，返回 SSE 流式响应 |
| **Agent 编排** | 新建 `chat_graph.py`，基于 LangGraph 的多轮状态图，支持意图路由（上传文件 / 问课程 / 要推荐 / 自由对话） |
| **会话状态** | 内存 dict 或 Redis，按 `session_id` 存储聊天历史 + 缺口分析结果 + 用户偏好 |
| **流式输出** | DeepSeek API 开启 `stream=True`，后端用 `StreamingResponse` 逐 token 推送到前端 |
| **前端 UI** | React 端改造为聊天界面：消息列表 + 底部输入框 + 文件上传入口，前端用 `fetch` + `ReadableStream` 解析 SSE |

#### 意图路由设计

```
用户消息 / 文件上传
  ↓
[LLM 意图识别]
  ├─ 上传文件 → 自动识别年级班级，触发 F1 缺口分析流程（OCR + 对比）
  ├─ 请求推荐 → 触发 F3 选课推荐
  ├─ 查询课程 → 触发 F4 课程信息查询
  └─ 自由对话 → LLM 直接回复（带上下文）
```

---

### F3 — 智能选课推荐

#### 触发方式

缺口分析完成后 Agent 主动询问，或用户在对话中主动请求。

#### 推荐依据

| 数据来源 | 用途 |
|----------|------|
| 缺口分析结果（F1 结构化输出） | 精确知道用户缺哪些课组、差多少学分、哪些必修课未修 |
| 用户偏好（对话中提取） | 如"喜欢软件类"、"想选水课"等倾向 |
| `course_schedule.json` | 课程的开课学期、学分、课组归属 |
| `prerequisites.json` | 课程先修关系（构建依赖图） |
| 培养方案结构化数据 | 各课组的学分要求 |

#### 核心创新：先修链拓扑分析

`services/prerequisite_graph.py` 负责构建课程依赖图并计算推荐优先级。

**数据格式** `data/courses/prerequisites.json`：
```json
[
  {"course": "数据结构", "prerequisites": ["程序设计基础"]},
  {"course": "操作系统", "prerequisites": ["数据结构", "计算机组成原理"]},
  {"course": "编译原理", "prerequisites": ["数据结构"]},
  {"course": "数据库系统", "prerequisites": ["数据结构"]},
  {"course": "计算机网络", "prerequisites": ["操作系统"]}
]
```

**依赖图可视化：**
```
程序设计基础 ──→ 数据结构 ──┬──→ 操作系统 ──→ 计算机网络
                             ├──→ 编译原理
                             └──→ 数据库系统
```

**阻塞系数计算：**

对每门未修课程，计算其"阻塞系数" = 该课程在依赖图中可达的后继节点数量（即不修这门课会阻塞多少后续课程）。

```python
# 示例：数据结构的阻塞系数
# 数据结构 → 操作系统, 编译原理, 数据库系统 (3门直接后继)
# 操作系统 → 计算机网络 (1门间接后继)
# 阻塞系数 = 3 + 1 = 4

# 程序设计基础（假设已修）：阻塞系数 = 0（已满足）
# 编译原理（未修）：阻塞系数 = 0（没有后继课程依赖它）
```

**推荐排序逻辑：**

```
1. 从缺口分析中提取待补课程列表（F1 结构化输出）
2. 筛选当前/下学期开课的课程
3. 检查先修关系是否满足（已修课程集合中是否包含所有先修）
4. 计算每门可修课程的阻塞系数
5. 按以下权重排序：
   - 必修 > 选修
   - 阻塞系数高的优先（不修会连锁阻塞后续选课）
   - 用户偏好匹配度（LLM 从对话中提取偏好关键词，与课程标签匹配）
6. LLM 基于排序结果生成自然语言推荐理由
```

**推荐效果示例：**

> "数据结构是你当前最优先要修的课。它是操作系统、编译原理、数据库系统 3 门课的先修课，如果这学期不修，下学期这 3 门课都无法选修。编译原理虽然也是缺口，但它不阻塞其他课程，可以延后考虑。"

**答辩话术：**

> "我们的选课推荐不是简单地'缺什么补什么'。系统构建了课程先修依赖图，通过拓扑排序计算每门课的'阻塞系数'——如果不修这门课，会导致多少后续课程无法选修。这样推荐出来的课程是全局最优的优先级，而不是局部的。别人要做到同样效果，不仅需要先修关系数据，还需要实现图算法和分析逻辑。"

---

### F4 — 课程信息查询

#### 可查询信息

| 字段 | 示例 | 数据来源 |
|------|------|---------|
| 开课学期 | 春季 / 秋季 | course_schedule.json |
| 先修课程 | 程序设计基础 | prerequisites.json |
| 考核方式 | 期中 + 期末 | course_details.json |
| 大作业 | 有 / 无，形式说明 | course_details.json |
| Presentation | 有 / 无 | course_details.json |
| 工作量评价 | 轻 / 中 / 重 | course_details.json（可选） |

#### 数据格式设计

`data/courses/course_details.json`：
```json
[
  {
    "course_code": "40130343",
    "course_name": "数据结构",
    "exam": {
      "midterm": true,
      "final": true
    },
    "assignments": {
      "homework": true,
      "project": true,
      "project_type": "个人编程项目",
      "presentation": false
    },
    "workload": "中等",
    "notes": "每周有编程作业，期末有上机考试"
  }
]
```

#### 实现方式

Agent 通过 Tool 调用 `course_info.py` 服务查询 JSON 数据，将结果交给 LLM 组织为自然语言回复。

#### 数据收集策略

- **MVP 阶段**：手动整理核心课程（约 20-30 门）的信息，覆盖未央书院常见课程
- **后续扩展**：可考虑爬取课程评教平台数据或收集学生问卷

---

### F5 — PDF MD5 缓存

#### 设计

```
上传 PDF
  ↓
计算文件 MD5 (hashlib.md5)
  ↓
查询 backend/cache/{md5}.md 是否存在
  ├─ 存在 → 直接读取 .md 返回（跳过 OCR，秒级响应）
  └─ 不存在 → 走 OCR 解析 → 结果写入 backend/cache/{md5}.md
```

#### 缓存元数据

`backend/cache/manifest.json`：
```json
{
  "abc123...": {
    "original_filename": "成绩单_张三.pdf",
    "cached_at": "2026-04-03T15:30:00",
    "file_size": 245678
  }
}
```

#### 清理策略

- 可选：设置缓存过期时间（如 30 天）
- 可选：限制缓存总大小，LRU 淘汰
- MVP 阶段不做清理，手动管理即可

---

## 四、技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 后端框架 | FastAPI + Uvicorn | 异步、自动 OpenAPI 文档 |
| Agent 编排 | LangGraph | 状态图驱动的多轮对话 |
| OCR | PaddleOCR 云端 API + 本地回退 | 云端优先，失败自动降级 |
| LLM | DeepSeek API（OpenAI 兼容） | 支持 stream 流式输出 |
| 前端 | React 18 + TypeScript + Vite + Tailwind | 聊天式 UI |
| 备选前端 | Streamlit | 快速验证用 |
| 缓存 | 文件系统（MD5 → .md 映射） | 轻量，无需额外依赖 |
| 课程数据 | JSON 文件 | 结构化课程信息，MVP 阶段手动维护 |

---

## 五、开发优先级

| 优先级 | 功能 | 依赖 | 预估复杂度 |
|--------|------|------|-----------|
| **P0** | F5 PDF 缓存 | 无，独立功能 | 低（~50 行） |
| **P0** | F1 结构化分析升级 | 无，独立于对话架构 | 中（解析器 + 计算逻辑） |
| **P0** | F2 多轮对话架构 | 无，基础架构 | 高（前后端均需改造） |
| **P1** | 先修链分析（prerequisite_graph） | F1 结构化输出 + prerequisites.json | 中（图算法） |
| **P1** | F3 选课推荐 | F2 + 先修链分析 + 课程数据 | 中 |
| **P2** | F4 课程信息查询 | F2 + 课程详情数据 | 中（数据收集是瓶颈） |

**推荐开发顺序**：

```
F5（缓存）          ──→ 独立，可立即开发
F1 结构化升级       ──→ 独立，可与 F5 并行
F2（对话架构）      ──→ F5/F1 完成后开始
先修链分析          ──→ 与 F2 并行（纯后端逻辑）
F3（推荐）          ──→ F2 + 先修链完成后开始
F4（课程查询）      ──→ F2 完成后开始，数据收集全程同步
```

**数据收集任务**（与开发并行）：
- `prerequisites.json`：整理核心课程的先修关系（约 30-50 门课）
- `course_details.json`：收集课程考核方式、工作量等信息（约 20-30 门课）
- `course_schedule.json`：整理开课学期、学分等基本信息

---

## 六、环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek API Key | — |
| `DEEPSEEK_BASE_URL` | DeepSeek API 地址 | `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | DeepSeek 模型 | `deepseek-chat` |
| `PADDLEOCR_DOC_PARSING_API_URL` | PaddleOCR 云端 API 地址 | `https://paddleocr.com/layout-parsing` |
| `PADDLEOCR_ACCESS_TOKEN` | PaddleOCR Token | — |
| `PADDLEOCR_DOC_PARSING_TIMEOUT` | OCR 超时（秒） | `600` |
| `POPPLER_PATH` | Poppler 路径（Windows 本地 OCR） | — |
| `HOST` | 后端监听地址 | `0.0.0.0` |
| `PORT` | 后端监听端口 | `8000` |
| `DEBUG` | 调试模式 | `false` |
