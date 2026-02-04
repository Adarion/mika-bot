# Mika-Bot

Mika-Bot 是一个基于大语言模型（LLM）的可扩展 IM 机器人框架，专为沉浸式角色扮演体验打造。

## ✨ 核心特性
- **🧠 强大的记忆系统**
  - **短期记忆**：基于上下文的流畅对话。
  - **长期记忆 (RAG)**：使用 ChromaDB 存储重要信息。

- **📊 现代化 WebUI**
  - **仪表盘**：实时监控 CPU、内存、QPS 等系统状态。
  - **配置管理**：图形化配置 LLM (OpenAI/Vertex) 和 IM (QQ Bot) 参数。
  - **聊天测试**：在网页上直接与机器人对话，调试 Prompt。

- **🔌 插件化架构**
  - **Agent 插件**：支持工具调用（联网搜索、系统操作）。
  - **Command 插件**：处理 `/ping`、`/role` 等指令。
  - **Scheduler 插件**：定时任务支持。

## 📂 项目结构

```
mika-bot/
├── main.py                 # 程序入口
├── config.yaml             # 核心配置文件 (Do not commit)
├── data/
│   ├── roles.yaml          # 角色 Prompt 配置 (支持热重载)
│   └── memory.db           # 记忆数据库
├── web/
│   ├── admin.py            # 后端 API Server
│   └── frontend/           # React 前端源码
├── core/                   # 核心框架 (EventBus, PluginManager)
├── adapters/               # 适配器 (LLM, QQ)
└── plugins/                # 功能插件
```

## 🚀 快速开始

### 1. 环境准备
- Python 3.10+
- Node.js 18+ (仅开发前端需要)
- QQ 开放平台机器人账号

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置
复制示例配置文件：
```bash
cp config.yaml.example config.yaml
```
编辑 `config.yaml` 填入你的 QQ Bot Token 和 LLM API Key。

### 4. 运行
```bash
python main.py
```
启动后访问 WebUI: `http://localhost:8080` (默认密码曾在安装时设置或见日志)。

### 5. 高级配置
- **角色设定**：修改 `data/roles.yaml` 可自定义 Prompt，修改后使用 `/reload_roles` 指令热加载。

## 🛠️ 开发指南

### 添加新插件
在 `plugins/` 目录下创建新文件，继承 `BasePlugin` 并实现 `on_load` 方法，最后在 `config.yaml` 中启用即可。

### 前端开发
前端代码位于 `web/frontend`，使用 React + Vite 构建。
```bash
cd web/frontend
npm install
npm run dev
```

## 📄 License
MIT
