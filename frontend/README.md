# Investigative Data Analyst 前端

本目录是 Investigative Data Analyst 的前端界面，提供数据上传、调查进度展示、结构化报告查看和交互式 drill-down 分析功能。

## 技术栈

| 技术 | 用途 |
|---|---|
| React 19 | UI 框架 |
| TypeScript | 类型安全 |
| Vite | 开发服务器与构建工具 |
| TailwindCSS | 样式系统 |
| React Router | 页面路由 |
| TanStack React Query | 数据获取与缓存 |
| Recharts | 图表可视化 |
| react-dropzone | 文件上传 |
| lucide-react | 图标库 |

## 前置条件

- Node.js 18+
- npm（随 Node.js 安装）
- 后端服务运行在 `http://localhost:8000`（前端通过 Vite proxy 转发 `/api` 请求）

## 安装与启动

```bash
cd frontend
npm install
npm run dev
```

开发服务器默认运行在 `http://localhost:5173`。如果 5173 端口被占用，Vite 会自动选择下一个可用端口。

Vite 配置（`vite.config.ts`）中已设置 proxy，将 `/api` 前缀的请求转发到后端 `http://localhost:8000`，因此前后端可以独立启动、分别调试。

## 可用脚本

| 命令 | 说明 |
|---|---|
| `npm run dev` | 启动开发服务器（HMR 热更新） |
| `npm run build` | 类型检查 + 生产构建，产物输出到 `dist/` |
| `npm run preview` | 预览生产构建结果 |
| `npm run lint` | 运行 Oxlint 代码检查 |

## 目录结构

```text
src/
├── api/                 API client 与共享类型定义
│   ├── task.ts          任务相关 API 请求
│   ├── upload.ts        上传 API 请求
│   └── types.ts         共享 TypeScript 类型
├── assets/              静态资源
├── components/          UI 组件
│   └── upload/          上传相关组件（UploadZone 等）
├── hooks/               自定义 Hooks
│   ├── useTaskPolling   任务轮询
│   ├── useTheme          主题切换
│   └── useUpload         上传逻辑
├── i18n/                国际化
│   ├── LanguageProvider  语言上下文 Provider
│   ├── zh.ts             中文翻译
│   ├── en.ts             英文翻译
│   └── translations.ts   翻译聚合
├── lib/                 工具函数
├── pages/               页面
│   ├── HomePage          首页（上传入口）
│   └── InvestigationPage 调查结果页（Overview / Findings / Narrative / Interactive）
├── App.tsx              根组件与路由配置
├── main.tsx            应用入口
└── index.css           全局样式与 TailwindCSS 导入
```

## 页面说明

### 首页（HomePage）

用户在此上传 CSV/Excel 文件，可选择性输入调查问题（如"为什么收入下降？"）。上传后系统创建后台任务并跳转到调查结果页。

### 调查结果页（InvestigationPage）

包含四个 tab：

| Tab | 内容 |
|---|---|
| Overview | 执行摘要、候选原因、数据集信息、质量摘要 |
| Findings | 按状态和置信度过滤的发现列表，可展开查看证据详情 |
| Narrative | LLM 生成的自然语言叙事，包括摘要、关键发现、建议 |
| Interactive | 后续调查问题、可运行的 drill-down 分析、数据缺口、调查路径 |

等待分析完成时，页面会显示当前 pipeline 阶段、阶段目标、输入输出和该阶段的重要性说明。

## 国际化

前端使用 i18n 支持中英文切换，所有用户可见文案均通过翻译文件管理，不硬编码语言字符串。

- 中文翻译：`src/i18n/zh.ts`
- 英文翻译：`src/i18n/en.ts`

新增用户可见文案时，需同时更新两个语言文件。

## 代理配置

`vite.config.ts` 中配置了开发代理：

```text
/api → http://localhost:8000
```

前端代码中所有 API 请求以 `/api` 为前缀，Vite 会自动转发到后端。生产环境部署时需要通过 Nginx 或反向代理实现同样的路径转发。
