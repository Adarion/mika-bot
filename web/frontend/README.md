# Mika-Bot WebUI (Admin Panel)

这是 Mika-Bot 的Web管理后台前端项目，基于 **React 18** + **Vite** 构建。

## ✨ 功能模块

- **仪表盘 (Dashboard)**
  - 实时监控服务器状态 (CPU, Memory, Swap, Disk)。
  - 查看机器人当前运行状态。

- **配置中心 (Configuration)**
  - **LLM 设置**：动态添加/修改 LLM 提供商 (API Key, Base URL)。
  - **IM 设置**：管理 QQ 机器人凭证 (AppID, Token)。

- **角色管理 (即将通过 WebUI 支持)**
  - 目前通过后端 API 和 YAML 配置，未来将支持可视化编辑 Prompt。

- **聊天调试 (Chat Console)**
  - 网页版模拟聊天窗口，直连 Bot 后端，方便测试 Prompt 和多轮对话逻辑。

## 🛠️ 技术栈

- **构建工具**: [Vite](https://vitejs.dev/)
- **框架**: [React](https://react.dev/)
- **路由**: [React Router](https://reactrouter.com/)
- **样式**: CSS Modules + Dark Mode Design System
- **API 通信**: Fetch API (with Custom Wrapper)

## 💻 开发指南

### 1. 安装依赖
```bash
npm install
```

### 2. 本地开发
```bash
npm run dev
```
开发服务器将运行在 `http://localhost:5173`。
> **注意**：需要在 `vite.config.js` 中配置 `proxy` 以转发 API 请求到后端 Python 服务 (默认 `http://localhost:8080`)。

### 3. 构建生产版本
```bash
npm run build
```
构建产物将输出到 `../dist` 目录。
Mika-Bot 的 Python 后端 (`web/admin.py`) 会自动检测并托管该目录下的静态文件，无需额外部署 Nginx。

## 📁 目录结构

```
src/
├── components/     # 公共组件 (Cards, Buttons, Layout)
├── contexts/       # 全局状态 (AuthContext)
├── pages/          # 页面视图 (Login, Dashboard, Chat...)
├── services/       # API 封装 (api.js)
├── App.jsx         # 路由配置
└── index.css       # 全局样式与变量
```
