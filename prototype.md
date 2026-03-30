# 选课助手智能体（培养方案协助）

## 项目结构

```text
Agent_competition/
├── README.md                      # 项目说明、环境要求、启动方式
├── .env.example                   # 环境变量模板（数据库 URL、API Key，勿提交真实密钥）
├── .gitignore
├── pyproject.toml                 # 或 requirements.txt：Python 依赖与版本约束
│
├── backend/                       # 后端服务（FastAPI）
│   ├── __init__.py
│   ├── main.py                    # 应用入口：挂载路由、CORS、生命周期
│   ├── config.py                  # 读取环境变量与配置
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py                # 依赖注入：DB Session、鉴权（若需要）
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py          # 健康检查
│   │       ├── advise.py          # 功能1：培养方案缺口 / 课组 / 学分
│   │       ├── teachers.py        # 功能2：按教师查课
│   │       └── search.py          # 功能3：方向模糊检索
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py             # 引擎、SessionLocal
│   │   └── base.py                # SQLAlchemy Base（若用 ORM）
│   ├── models/                    # ORM 模型（与表一一对应，可选）
│   │   └── ...
│   ├── schemas/                   # Pydantic 请求/响应体
│   │   ├── advise.py
│   │   ├── course.py
│   │   └── ...
│   ├── services/                  # 业务逻辑（无 HTTP 细节，便于单测）
│   │   ├── graduation.py          # 未修课、课组完成度、学分差计算
│   │   ├── teacher_courses.py
│   │   ├── course_search.py       # 关键词 / 标签 / 向量检索封装
│   │   └── recommendation.py      # 选课推荐打分与排序（规则 + 可选 LLM 润色）
│   └── agent/                     # 智能体编排（LangGraph 等）
│       ├── __init__.py
│       ├── graph.py               # 状态机 / 节点定义
│       ├── tools.py               # 暴露给模型的工具：调用 services + API
│       ├── prompts.py             # 系统提示词与模板
│       └── runner.py              # 单次对话入口（供 API 或前端调用）
│
├── db/
│   ├── migrations/                # Alembic 迁移（若使用）
│   │   └── versions/
│   ├── schema.sql                 # 初始化 DDL（可选，与迁移二选一或并存）
│   └── seed/                      # 演示用种子数据
│       └── sample_data.sql
│
├── frontend/                      # 演示界面（择一或并存）
│   ├── streamlit_app/             # Streamlit：最快答辩 Demo
│   │   └── app.py
│   └── web/                       # 若用 React/Vite
│       ├── package.json
│       └── src/
│
├── scripts/                       # 一次性脚本
│   ├── init_db.py                 # 建表 / 灌数
│   └── embed_courses.py           # 课程简介向量化写入 pgvector（若启用）
│
├── tests/
│   ├── conftest.py
│   ├── test_graduation_service.py
│   ├── test_api_advise.py
│   └── test_agent_tools.py
│
└── docs/
    ├── data_model.md              # ER 说明、培养方案版本约定
    └── api.md                     # OpenAPI 摘要或对接说明
```

## 结构说明（简要）

| 目录/文件 | 作用 |
|-----------|------|
| `backend/api` | 对外 HTTP 接口，薄层，复杂逻辑下沉到 `services`。 |
| `backend/services` | 培养方案计算、检索、推荐规则，**可单测、不依赖 LLM**。 |
| `backend/agent` | 自然语言理解、多轮对话、**只通过 tools 访问真实数据**，避免幻觉。 |
| `db` | 表结构、迁移与种子数据，与学校培养方案版本强绑定。 |
| `frontend` | 答辩演示；初期可用 Streamlit 直连 `backend` API。 |
| `tests` | 优先覆盖 `graduation` 与 API 契约，保证评分口径稳定。 |

---

*后续可在本文件补充：环境变量列表、本地启动命令、赛方提交的目录约定。*
