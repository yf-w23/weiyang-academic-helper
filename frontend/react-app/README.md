# 未央书院学业规划助手 - 前端（React）

当前前端已从“单页上传分析”演进为**对话式主界面**，默认入口为聊天页面，支持成绩单上传和多会话管理（默认非流式回复）。

## 当前功能概览

- **对话式学业助手**：在聊天中提问培养方案、通识课、课程查询与推荐问题
- **成绩单上传**：在聊天上下文中上传 PDF，并返回解析结果与后续建议
- **多会话管理**：侧边栏新建/切换/删除会话，消息历史本地持久化（Zustand persist）
- **Markdown 渲染**：助手回复支持 Markdown（含 GFM）
- **流式能力保留**：已接入 SSE 接口，当前 UI 默认走非流式发送
- **后端对接**：对接 `/api/chat/*` 与 `/api/advise/gap-analysis`

## 路由说明

- `/`：主入口，`ChatPage`（当前默认使用）
- `/legacy`：历史页面，`HomePage`（保留兼容，不作为主流程）

## 技术栈

- **框架**: React 18 + TypeScript
- **构建工具**: Vite 5
- **状态管理**: Zustand（含本地持久化）
- **网络请求**: Axios + Fetch（SSE 流式）
- **样式**: Tailwind CSS
- **Markdown**: react-markdown + remark-gfm + rehype-raw
- **图标/交互**: lucide-react + react-dropzone

## 快速开始

### 1) 安装依赖

```bash
cd frontend/react-app
npm install
```

### 2) 配置环境变量

在 `frontend/react-app` 下创建 `.env.local`：

```env
VITE_API_BASE_URL=http://localhost:8000
```

### 3) 启动开发服务

```bash
npm run dev
```

默认访问（以 Vite 输出为准）：`http://localhost:3000` 或 `http://localhost:5173`。

### 4) 构建与预览

```bash
npm run build
npm run preview
```

## 前后端接口（当前实际使用）

- `POST /api/chat/message`：非流式聊天
- `POST /api/chat/message/stream`：SSE 流式聊天（能力保留，当前默认不走）
- `POST /api/chat/upload`：聊天场景上传成绩单
- `GET /api/chat/history/{session_id}`：获取会话历史
- `DELETE /api/chat/session/{session_id}`：清空会话
- `POST /api/advise/gap-analysis`：单轮上传并分析（保留）

## 目录结构（精简）

```text
frontend/react-app/
├── src/
│   ├── api/
│   │   └── client.ts          # API 客户端（Axios + SSE）
│   ├── store/
│   │   └── chatStore.ts       # 会话与消息状态管理
│   ├── pages/
│   │   ├── ChatPage.tsx       # 主聊天页（默认入口）
│   │   └── HomePage.tsx       # Legacy 页面（/legacy）
│   ├── components/
│   │   ├── Layout.tsx
│   │   ├── ResultDisplay.tsx
│   │   ├── Hero.tsx
│   │   └── UploadForm.tsx
│   ├── App.tsx                # 路由定义
│   ├── main.tsx
│   └── index.css
├── package.json
└── README.md
```

## 备注

- 当前产品主路径是 `ChatPage`，README 以现状维护。
- `HomePage`/`Hero`/`UploadForm` 仍保留，便于回溯旧交互方案或继续迭代。
