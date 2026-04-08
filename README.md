# 未央书院学业规划助手

基于 LangGraph + FastAPI + DeepSeek API 的智能学业规划助手。支持多轮对话式交互，自动识别成绩单信息，进行培养方案缺口分析、课程推荐和课程信息查询。

## 功能特性

### 核心功能

| 功能 | 描述 | 状态 |
|------|------|------|
| 📄 **PDF 成绩单解析** | 使用 PaddleOCR 云端 API 精准解析 PDF 成绩单，支持 MD5 缓存加速 | ✅ 已实现 |
| 🎯 **自动信息识别** | 自动从成绩单中提取入学年份和班级信息（如 `未央-电31`） | ✅ 已实现 |
| 📊 **培养方案缺口分析** | 对比已修课程与培养方案，生成详细的缺口分析报告 | ✅ 已实现 |
| 🎨 **通识课组分析** | 针对人文、社科、艺术、科学四大课组的完成情况进行专项分析 | ✅ 已实现 |
| 💬 **多轮对话交互** | DeepSeek 风格聊天界面，支持流式输出 | ✅ 已实现 |
| 🎓 **智能选课推荐** | 基于缺口分析 + 全校课程数据库，结合用户偏好推荐课程 | ✅ 已实现 |
| 🔍 **课程信息查询** | 查询课程详情、教师信息、开课学期、考核方式等 | ✅ 已实现 |
| 🗂️ **课程数据爬虫** | 从清华大学选课系统爬取课程信息（Puppeteer） | ✅ 已实现 |

### 技术创新点

| 创新点 | 说明 |
|--------|------|
| **结构化精确分析** | 培养方案和成绩单解析为结构化数据，代码层面精确计算学分，LLM 只负责生成自然语言报告，结果可验证、可复现 |
| **先修链拓扑排序** | 构建课程先修依赖图，计算每门课的"阻塞系数"，推荐课程考虑全局最优优先级 |
| **MD5 缓存机制** | 相同成绩单 MD5 命中时跳过 OCR，秒级响应 |

---

## 项目结构

```
Agent_competition/
├── backend/                        # FastAPI 后端
│   ├── main.py                    # 应用入口
│   ├── config.py                  # 配置管理（pydantic-settings）
│   │
│   ├── api/                       # API 路由层
│   │   ├── deps.py               # 依赖注入
│   │   └── routes/
│   │       ├── health.py         # 健康检查 GET /health
│   │       ├── advise.py         # 单轮缺口分析 POST /api/advise/gap-analysis
│   │       └── chat.py           # 多轮对话 API /api/chat/*
│   │
│   ├── agent/                     # LangGraph Agent 编排
│   │   ├── graph.py              # 单轮分析状态图
│   │   ├── chat_graph.py         # 多轮对话状态图（含意图路由）
│   │   ├── chat_runner.py        # 对话会话管理
│   │   ├── runner.py             # 单轮分析入口
│   │   ├── tools.py              # Agent 工具（OCR、方案加载）
│   │   ├── prompts.py            # 单轮提示词模板
│   │   └── chat_prompts.py       # 对话提示词模板
│   │
│   ├── services/                  # 业务逻辑服务
│   │   ├── graduation.py         # 培养方案加载（2021-2025 级）
│   │   ├── transcript_parser.py  # 成绩单结构化解析 + 信息提取
│   │   ├── gap_calculator.py     # 精确缺口计算（代码层面）
│   │   ├── prerequisite_graph.py # 先修链分析与拓扑排序
│   │   ├── course_data_service.py # 课程数据查询服务
│   │   ├── recommendation.py     # 选课推荐算法
│   │   ├── cache_service.py      # PDF MD5 缓存服务
│   │   ├── ocr_service.py        # OCR 服务（云端优先，本地回退）
│   │   ├── ocr_service_local.py  # 本地 OCR（PaddleOCR）
│   │   └── llm_service.py        # DeepSeek API 封装
│   │
│   ├── schemas/                   # Pydantic 请求/响应模型
│   │   └── advise.py
│   │
│   ├── data/                      # 结构化数据
│   │   └── courses/
│   │       ├── courses.json          # 全校课程数据库
│   │       ├── course_schedule.json  # 开课学期信息
│   │       └── prerequisites.json    # 课程先修关系
│   │
│   ├── DegreeRequirements/        # 培养方案 Markdown 文件
│   │   ├── 2021未央书院培养方案.md
│   │   ├── 2022未央书院培养方案.md
│   │   ├── 2023未央书院培养方案.md
│   │   ├── 2024未央书院培养方案.md
│   │   └── 2025未央书院培养方案.md
│   │
│   ├── cache/                     # OCR 结果缓存目录
│   └── utils/
│       └── file_utils.py
│
├── frontend/
│   └── react-app/                 # React 前端（Vite + TypeScript + Tailwind）
│       ├── src/
│       │   ├── App.tsx           # 应用主组件
│       │   ├── main.tsx          # 入口
│       │   ├── pages/
│       │   │   ├── ChatPage.tsx      # 对话页面（主界面）
│       │   │   └── HomePage.tsx      # 首页（可选）
│       │   ├── components/
│       │   │   ├── Layout.tsx        # 布局组件
│       │   │   ├── Hero.tsx          # Hero 区域
│       │   │   ├── UploadForm.tsx    # 文件上传表单
│       │   │   └── ResultDisplay.tsx # 结果展示
│       │   ├── store/
│       │   │   └── chatStore.ts      # Zustand 状态管理
│       │   ├── api/
│       │   │   └── client.ts         # API 客户端
│       │   └── types/
│       │       └── index.ts          # TypeScript 类型定义
│       ├── package.json
│       └── vite.config.ts
│
├── info_crawler/                  # 课程信息爬虫工具集
│   ├── download_all_courses.js    # 下载所有课程信息
│   ├── extract_teacher_mapping.js # 提取教师映射表
│   └── README.md                  # 爬虫使用说明
│
├── scripts/                       # 测试脚本
│   ├── test_ocr.py
│   └── test_ocr_api.py
│
├── pyproject.toml                 # Python 依赖配置
├── .env.example                   # 环境变量模板
└── README.md                      # 本文件
```

---

## 快速开始

### 1. 安装依赖

```bash
# 后端依赖
pip install -e .

# 前端依赖
cd frontend/react-app
npm install
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# DeepSeek API（用于 LLM 分析）
DEEPSEEK_API_KEY=your-deepseek-api-key

# PaddleOCR 云端 API（用于 OCR）
PADDLEOCR_ACCESS_TOKEN=your-paddleocr-token
```

### 3. 启动后端服务

```bash
python -m backend.main
```

服务启动后访问 http://localhost:8000/docs 查看 API 文档。

### 4. 启动前端

```bash
cd frontend/react-app
npm run dev
```

访问 http://localhost:3000

---

## API 文档

### 多轮对话接口

#### 发送消息（非流式）
```bash
POST /api/chat/message
Content-Type: application/json

{
  "session_id": "optional-session-id",
  "message": "分析我的培养方案"
}
```

#### 发送消息（SSE 流式）
```bash
POST /api/chat/message/stream
Content-Type: application/json

{
  "session_id": "optional-session-id",
  "message": "推荐下学期课程"
}
```

#### 上传成绩单
```bash
POST /api/chat/upload
Content-Type: multipart/form-data

transcript: <PDF 文件>
session_id: optional-session-id
```

#### 获取对话历史
```bash
GET /api/chat/history/{session_id}
```

### 单轮分析接口（保留）

```bash
POST /api/advise/gap-analysis
Content-Type: multipart/form-data

transcript: <PDF 文件>
```

---

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端框架 | FastAPI + Uvicorn |
| Agent 编排 | LangGraph（状态图驱动） |
| LLM | DeepSeek API（OpenAI 兼容接口，支持流式） |
| OCR | PaddleOCR 云端 API（自动回退到本地 PaddleOCR） |
| 前端 | React 18 + TypeScript + Vite + Tailwind CSS |
| 状态管理 | Zustand |
| 爬虫 | Puppeteer |
| 缓存 | 文件系统（MD5 → .md 映射） |

---

## 工作流程

### 多轮对话流程

```
用户发送消息 / 上传文件
        ↓
[意图识别] LLM 判断用户意图
        ↓
    ├─ 上传文件 → 自动识别年级班级，提取成绩单
    ├─ 请求分析 → 触发缺口分析流程
    ├─ 请求推荐 → 触发选课推荐
    ├─ 查询课程 → 查询课程数据库
    └─ 自由对话 → LLM 直接回复
        ↓
[执行对应节点] 生成回复
        ↓
返回流式 / 非流式响应
```

### 缺口分析流程

```
用户上传 PDF 成绩单
        ↓
[检查缓存] MD5 匹配 → 直接返回缓存结果
        ↓
[OCR 提取] PaddleOCR 云端/本地提取文本
        ↓
[信息识别] 自动提取年级、班级、已修课程
        ↓
[结构化解析] 成绩单 → 课程列表，培养方案 → 课程树
        ↓
[精确计算] 代码计算学分差、完成率、缺课
        ↓
[LLM 生成报告] 输入结构化数据 → 自然语言报告
        ↓
返回分析结果
```

### 通识选修课组分析

未央书院通识选修课包含四大课组，系统会针对每个课组进行专项分析：

| 课组 | 最低学分要求 | 课程数量 | 说明 |
|------|-------------|---------|------|
| 🔬 **科学课组** | 3 学分 | 277+ 门 | 未央书院要求比其他课组多 1 学分 |
| 📚 **人文课组** | 2 学分 | 138+ 门 | 含必修《科技与人文研讨课》（1学分） |
| 🏛️ **社科课组** | 2 学分 | 140+ 门 | 社会科学类通识课程 |
| 🎨 **艺术课组** | 2 学分 | 202+ 门 | 音乐、美术、戏剧等艺术类课程 |

**总学分要求**: 至少 11 学分（四组最低要求 3+2+2+2=9 学分，需额外选修 2 学分）

**分析逻辑**:
```
已修课程
    ↓
匹配四大课组课程库（课程号/课程名模糊匹配）
    ↓
计算各课组已修学分
    ↓
判断是否满足最低要求
    ↓
生成课组完成报告 + 选课建议
```

---

## 配置说明

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek API Key | - |
| `DEEPSEEK_BASE_URL` | DeepSeek API 地址 | `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | DeepSeek 模型名称 | `deepseek-chat` |
| `PADDLEOCR_DOC_PARSING_API_URL` | PaddleOCR 云端 API 地址 | `https://paddleocr.com/layout-parsing` |
| `PADDLEOCR_ACCESS_TOKEN` | PaddleOCR Access Token | - |
| `PADDLEOCR_DOC_PARSING_TIMEOUT` | OCR 请求超时时间（秒） | `600` |
| `POPPLER_PATH` | Poppler 路径（Windows 本地 OCR） | - |
| `HOST` | 后端监听地址 | `0.0.0.0` |
| `PORT` | 后端监听端口 | `8000` |
| `DEBUG` | 调试模式 | `false` |

---

## 支持的培养方案

| 入学年份 | 培养方案文件 |
|----------|--------------|
| 2021 级 | `backend/DegreeRequirements/2021未央书院培养方案.md` |
| 2022 级 | `backend/DegreeRequirements/2022未央书院培养方案.md` |
| 2023 级 | `backend/DegreeRequirements/2023未央书院培养方案.md` |
| 2024 级 | `backend/DegreeRequirements/2024未央书院培养方案.md` |
| 2025 级 | `backend/DegreeRequirements/2025未央书院培养方案.md` |

---

## 课程数据爬虫

位于 `info_crawler/` 目录，用于从清华大学选课系统爬取课程信息。

### 使用步骤

1. 安装依赖：`npm install puppeteer-core iconv-lite`
2. 启动 Chrome 调试模式（添加 `--remote-debugging-port=9222`）
3. 登录选课系统，进入"选课开课信息查询"页面
4. 运行爬虫：`node info_crawler/download_all_courses.js`

详见 [info_crawler/README.md](info_crawler/README.md)

---

## 开发计划

- [x] PDF 成绩单 OCR 解析
- [x] 自动识别年级班级信息
- [x] 培养方案缺口分析
- [x] MD5 缓存机制
- [x] 结构化缺口计算
- [x] 多轮对话架构
- [x] 课程数据库
- [x] 选课推荐功能
- [x] 课程信息查询
- [x] 先修链拓扑分析
- [x] 课程信息爬虫

---


