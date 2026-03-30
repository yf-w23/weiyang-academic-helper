# 未央书院培养方案缺口分析助手 - React 前端

**现代学院风设计** - 采用独特审美方向的前端应用。

## 设计特点

### 审美方向
- **风格**：现代学院风 (Modern Academic)
- **设计理念**：结合学术严谨性与现代精致感
- **调性**：优雅、专业、有质感

### 视觉元素
- **字体**：
  - 标题：Playfair Display (优雅衬线体)
  - 正文：DM Sans (现代无衬线)
- **配色**：
  - 主色：深海军蓝 (#1f2839)
  - 强调色：琥珀金 (#d97706)
  - 背景色：奶油白 (#fefdfb)
- **装饰元素**：
  - 对角线装饰
  - 几何角标
  - 噪点纹理叠加
  - 浮动几何图形

### 动画效果
- 页面加载渐入动画
- 交错子元素动画
- 悬浮上升效果
- SVG 路径绘制动画
- 平滑过渡效果

## 技术栈

- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **样式**: Tailwind CSS + 自定义 CSS
- **图标**: Lucide React
- **文件上传**: react-dropzone

## 快速开始

### 1. 安装依赖

```bash
cd frontend/react-app
npm install
```

### 2. 配置环境变量

```bash
cp .env.example .env.local
```

编辑 `.env.local`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

### 3. 启动开发服务器

```bash
npm run dev
```

访问：`http://localhost:3000`

### 4. 构建生产版本

```bash
npm run build
```

## 项目结构

```
frontend/react-app/
├── public/
│   └── logo.svg              # 学院风 logo
├── src/
│   ├── api/
│   │   └── client.ts         # API 客户端
│   ├── components/
│   │   ├── Layout.tsx        # 布局组件
│   │   ├── Hero.tsx          # 首页 Hero 区域
│   │   ├── UploadForm.tsx    # 上传表单
│   │   └── ResultDisplay.tsx # 结果显示
│   ├── pages/
│   │   └── HomePage.tsx      # 首页
│   ├── types/
│   │   └── index.ts          # 类型定义
│   ├── lib/
│   │   └── utils.ts          # 工具函数
│   ├── App.tsx
│   ├── index.css             # 全局样式
│   └── main.tsx
├── index.html
├── tailwind.config.js        # Tailwind 配置
├── package.json
└── README.md
```

## 设计亮点

1. **独特的字体组合**：Playfair Display + DM Sans
2. **精心设计的配色**：深海军蓝与琥珀金的经典搭配
3. **丰富的装饰元素**：对角线、角标、噪点纹理
4. **流畅的动画**：使用 cubic-bezier 曲线的高级动画
5. **响应式设计**：完美适配各种屏幕尺寸
6. **无障碍访问**：清晰的对比度和语义化 HTML

## 注意事项

- 使用 Google Fonts 加载字体，确保网络连接正常
- 动画效果使用 CSS 实现，性能友好
- 支持深色/浅色模式切换（可扩展）
