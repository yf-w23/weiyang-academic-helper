# 未央书院培养方案缺口分析助手

基于 LangGraph + FastAPI + PaddleOCR 云端 API + DeepSeek API 的智能学业规划助手。

## 功能

- **培养方案缺口分析**：上传成绩单 PDF，自动对比培养方案，识别未修课程
- **云端 OCR**：使用 PaddleOCR 云端 API 精准解析 PDF 成绩单
- **智能分析**：使用 DeepSeek LLM 进行培养方案缺口分析

## 项目结构

```
Agent_competition/
├── backend/                    # FastAPI 后端
│   ├── api/                   # API 路由
│   ├── agent/                 # LangGraph Agent 编排
│   ├── services/              # 业务逻辑服务
│   │   ├── graduation.py      # 培养方案加载
│   │   ├── ocr_service.py     # PaddleOCR 云端 API 封装
│   │   └── llm_service.py     # DeepSeek API 封装
│   ├── schemas/               # Pydantic 模型
│   ├── paddleocr_doc_parsing/ # PaddleOCR 文档解析库
│   ├── config.py              # 配置管理
│   └── main.py                # 应用入口
├── frontend/                  # 前端
│   ├── react-app/            # React 清新风格前端（推荐）
│   └── streamlit_app/        # 原 Streamlit 前端
├── pyproject.toml             # Python 依赖
├── .env.example               # 环境变量模板
└── README.md                  # 本文件
```

## 快速开始

### 1. 安装依赖

```bash
pip install -e .
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 API Key：

```env
# DeepSeek API（用于 LLM 分析）
DEEPSEEK_API_KEY=sk-42c0cbf092e8445d9c124045df21934a

# PaddleOCR 云端 API（用于 OCR）
PADDLEOCR_ACCESS_TOKEN=c76347ab2a8162aeafe6afbbb73eff7eee2330eb
```

### 3. 启动后端服务

```bash
python -m backend.main
```

服务启动后访问：`http://localhost:8000/docs` 查看 API 文档。

### 4. 启动前端（React 新版，推荐）

```bash
cd frontend/react-app
npm install
npm run dev
```

访问：`http://localhost:3000`

### 5. 启动前端（Streamlit 旧版）

```bash
cd frontend/streamlit_app
streamlit run app.py
```

访问：`http://localhost:8501`

## API 使用

### 培养方案缺口分析

```bash
curl -X POST "http://localhost:8000/api/advise/gap-analysis" \
  -F "enrollment_year=2023" \
  -F "class_name=未央-机械31" \
  -F "transcript=@成绩单.pdf"
```

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端框架 | FastAPI |
| Agent 编排 | LangGraph |
| OCR | PaddleOCR 云端 API |
| LLM | DeepSeek API |
| 前端（新）| React + TypeScript + Tailwind CSS |
| 前端（旧）| Streamlit |

## React 前端特点

- **清新设计**：蓝紫渐变色系，简洁现代
- **流畅交互**：拖拽上传、进度显示、动画效果
- **响应式布局**：完美适配桌面端和移动端
- **专业图标**：使用 Lucide React 图标库，替代 Emoji
- **TypeScript**：类型安全，更好的开发体验

## 配置说明

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek API Key | - |
| `DEEPSEEK_BASE_URL` | DeepSeek API 地址 | https://api.deepseek.com |
| `DEEPSEEK_MODEL` | DeepSeek 模型 | deepseek-chat |
| `PADDLEOCR_DOC_PARSING_API_URL` | PaddleOCR API 地址 | https://paddleocr.com/layout-parsing |
| `PADDLEOCR_ACCESS_TOKEN` | PaddleOCR Token | - |
| `PADDLEOCR_DOC_PARSING_TIMEOUT` | OCR 超时时间 | 600 秒 |

## 流程说明

```
用户上传 PDF 成绩单
        ↓
[FastAPI] 接收文件
        ↓
[LangGraph Node: extract_transcript] 
        → 调用 PaddleOCR 云端 API 提取文本
        ↓
[LangGraph Node: load_schema]
        → 根据年份加载培养方案 MD 文件
        ↓
[LangGraph Node: analyze_gap]
        → 调用 DeepSeek API 对比分析
        ↓
返回缺口分析报告
```
