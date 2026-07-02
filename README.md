<div align="center">

# 📚 StudyMate 智学助手

> 让学习更智慧，让备考更轻松

[![Vue](https://img.shields.io/badge/Vue-3.x-4FC08D?style=flat-square&logo=vue.js&logoColor=white)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)
[![Electron](https://img.shields.io/badge/Electron-29.x-47848F?style=flat-square&logo=electron&logoColor=white)](https://www.electronjs.org/)

</div>

## 🌟 项目简介

**StudyMate 智学助手** 是一款基于人工智能技术的开源智能学习辅助工具，采用现代化的前后端分离架构，结合先进的学习科学理论，为学生提供全方位的学习支持。从笔记管理到智能备考计划，从知识图谱到文献阅读，StudyMate 致力于打造一站式智能学习解决方案。

### ✨ 核心亮点

- 🤖 **AI 驱动**：深度集成大语言模型，支持多厂商 API 配置
- 📝 **智能笔记**：Markdown 编辑器 + 自动闪卡生成 + 知识图谱
- 🎯 **个性备考**：多轮诊断评估，AI 定制专属学习计划
- 🌙 **深色模式**：全局深色主题，护眼舒适
- 💾 **本地优先**：数据本地存储，隐私安全有保障
- 🖥️ **跨平台**：支持 Web 浏览器与 Electron 桌面应用

## 📋 功能特性

### 📝 笔记闪卡模块

| 功能 | 描述 |
|------|------|
| **知识库管理** | 多级文件夹结构，笔记标签分类，全文搜索 |
| **Markdown 编辑** | 实时预览，公式支持（KaTeX），代码高亮 |
| **AI 笔记整理** | 自动结构化笔记，提取关键知识点 |
| **智能闪卡** | 自动生成问答闪卡，SM-2 记忆算法 |
| **知识图谱** | 可视化知识关联，交互式节点探索 |
| **导入导出** | 支持 Markdown 批量导入导出 |

### 🎯 备考计划模块

| 功能 | 描述 |
|------|------|
| **多轮诊断** | 三轮智能评估，精准定位薄弱环节 |
| **AI 计划生成** | 个性化每日计划，分阶段复习策略 |
| **进度追踪** | 打卡热力图，备考火力值，成就系统 |
| **紧急救援** | 进度落后自动生成补救方案 |
| **详细规划** | 3-5 个学习阶段，具体到天的任务安排 |

### 📚 课程管理模块

| 功能 | 描述 |
|------|------|
| **课程创建** | 自定义课程信息，目标分数设置 |
| **知识点管理** | 多级知识树，掌握度标记 |
| **学习统计** | 笔记数量，闪卡数量，活力值进度 |

### 📖 文献管理模块

| 功能 | 描述 |
|------|------|
| **PDF 阅读** | 内置 PDF 阅读器，分页浏览 |
| **文献整理** | 文件夹分类，标签管理，搜索筛选 |
| **AI 速读** | 五段论论文速读报告，一键提取核心 |

### ⚙️ AI 配置中心

| 功能 | 描述 |
|------|------|
| **多厂商支持** | DeepSeek、OpenAI、通义千问、智谱AI 等 |
| **模型切换** | 快捷切换不同模型，平衡效果与成本 |
| **本地存储** | API Key 仅存浏览器 localStorage，安全可靠 |
| **自定义配置** | 支持自定义 Base URL，兼容各类兼容 API |

## 🛠️ 技术栈

### 前端

- **框架**：Vue 3 + Composition API
- **UI 组件库**：Vant 4（移动优先设计）
- **构建工具**：Vite 5
- **路由**：Vue Router 4
- **HTTP 客户端**：Axios
- **Markdown**：Marked + Highlight.js
- **数学公式**：KaTeX + MathLive
- **图表**：ECharts 6
- **PDF 阅读**：PDF.js
- **桌面应用**：Electron 29

### 后端

- **Web 框架**：FastAPI
- **ORM**：SQLAlchemy 2.x
- **数据库**：SQLite（轻量零配置）
- **数据验证**：Pydantic
- **AI 客户端**：httpx（异步 HTTP 请求）
- **服务器**：Uvicorn（ASGI）

## 📁 项目结构

```
studymate/
├── backend/                  # FastAPI 后端
│   ├── main.py              # 应用入口，全局中间件
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库连接与初始化
│   ├── models.py            # SQLAlchemy 数据模型
│   ├── schemas.py           # Pydantic 请求/响应模型
│   ├── requirements.txt     # Python 依赖
│   ├── ai/
│   │   └── client.py        # AI 客户端封装
│   └── routers/             # API 路由
│       ├── notes.py         # 笔记相关接口
│       ├── papers.py        # 文献相关接口
│       ├── plans.py         # 备考计划接口
│       ├── review.py        # 闪卡复习接口
│       ├── courses.py       # 课程管理接口
│       └── images.py        # 图片处理接口
│
├── frontend/                 # Vue 3 前端
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.js          # 应用入口
│       ├── App.vue          # 根组件
│       ├── api/             # API 请求封装
│       ├── views/           # 页面组件
│       │   ├── Notes.vue    # 笔记闪卡页
│       │   ├── Plans.vue    # 备考计划页
│       │   ├── Courses.vue  # 课程管理页
│       │   └── Literature.vue # 文献管理页
│       ├── components/      # 通用组件
│       │   ├── AIConfigPanel.vue    # AI 配置面板
│       │   ├── ModelQuickSwitch.vue # 模型快速切换
│       │   ├── SettingsDrawer.vue   # 设置抽屉
│       │   ├── FolderTree.vue       # 文件夹树
│       │   ├── MarkdownViewer.vue   # Markdown 预览
│       │   ├── GraphView.vue        # 知识图谱
│       │   └── ...
│       ├── utils/           # 工具函数
│       │   ├── aiConfig.js  # AI 配置管理
│       │   ├── theme.js     # 主题切换
│       │   └── localSync.js # 本地同步
│       ├── styles/          # 全局样式
│       │   └── theme.css    # 主题变量
│       ├── router/          # 路由配置
│       └── data/            # 静态数据
│
├── electron/                 # Electron 桌面应用
│   ├── main.js              # 主进程
│   └── preload.js           # 预加载脚本
│
├── package.json              # 项目根配置
├── start-dev.js             # 开发模式启动脚本
├── build.bat                # Windows 打包脚本
└── README.md
```

## 🚀 快速开始

### 环境要求

- **Node.js** >= 16.0.0
- **Python** >= 3.9
- **npm** 或 **pnpm** / **yarn**

### 方法一：一键启动（推荐）

#### Windows

双击运行 `开发模式启动.bat`，等待两个窗口都启动后访问 http://localhost:5173

#### 命令行

```bash
# 安装根依赖
npm install

# 同时启动前后端
npm run dev
```

### 方法二：手动启动

#### 1. 启动后端服务

```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv venv

# Windows 激活
venv\Scripts\activate

# macOS / Linux 激活
# source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py
# 或使用 uvicorn
# uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端启动后访问：http://localhost:8000/docs 查看 API 文档

#### 2. 启动前端服务

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端启动后访问：http://localhost:5173

### 验证安装

1. 打开浏览器访问 http://localhost:5173
2. 查看底部状态栏，后端连接状态应为「已连接」
3. 尝试创建一条笔记，确认数据可以正常保存

## ⚙️ AI 配置

StudyMate 支持多种大语言模型 API，**所有配置均存储在本地浏览器中**，不会上传到任何服务器。

### 配置步骤

1. 点击页面右上角的「设置」按钮
2. 选择「AI 模型设置」
3. 选择你的 AI 服务商
4. 填入 API Key 和 Base URL（如需要）
5. 选择默认模型
6. 点击「测试连接」验证配置

### 支持的 AI 厂商

| 厂商 | 推荐模型 | 官方地址 |
|------|---------|---------|
| **DeepSeek** | deepseek-v4-pro / deepseek-v4-flash | [deepseek.com](https://www.deepseek.com/) |
| **OpenAI** | gpt-4o / gpt-3.5-turbo | [openai.com](https://openai.com/) |
| **通义千问** | qwen-plus / qwen-turbo | [tongyi.aliyun.com](https://tongyi.aliyun.com/) |
| **智谱AI** | glm-4 / glm-4-flash | [zhipuai.cn](https://www.zhipuai.cn/) |
| **更多** | 支持任何 OpenAI 兼容 API | - |

> 💡 **提示**：如果你使用的是其他兼容 OpenAI 格式的 API 服务，可以选择「自定义」并填入对应的 Base URL。

## 🎨 深色模式

StudyMate 支持全局深色模式，保护你的眼睛：

- 点击右上角设置 → 切换「深色模式」开关
- 所有页面和组件均已适配深色主题
- Vant UI 组件库深度适配
- 选择自动跟随系统或手动切换

## 📦 打包部署

### 构建前端

```bash
cd frontend
npm run build
```

构建产物输出到 `frontend/dist/` 目录

### 打包后端（Windows）

使用 PyInstaller 打包为独立可执行文件：

```bash
cd backend
pyinstaller --onefile --name main main.py
```

输出到 `dist/main.exe`

### 打包 Electron 桌面应用

```bash
# 确保前端已构建
npm run build

# 打包 Windows 应用
npm run electron:build:win
```

安装包输出到 `release-final-v2/` 目录

## 🧩 API 接口

### 主要接口列表

| 模块 | 方法 | 路径 | 描述 |
|------|------|------|------|
| **系统** | GET | `/api/test-connection` | 测试后端连接 |
| **AI** | POST | `/api/ai/chat` | 通用 AI 对话 |
| | POST | `/api/ai/analyze-pdf` | PDF 论文速读分析 |
| **笔记** | GET | `/api/notes/` | 获取笔记列表 |
| | POST | `/api/notes/` | 创建笔记 |
| | GET | `/api/notes/{id}` | 获取笔记详情 |
| | PUT | `/api/notes/{id}` | 更新笔记 |
| | DELETE | `/api/notes/{id}` | 删除笔记 |
| **课程** | GET | `/api/courses/` | 获取课程列表 |
| | POST | `/api/courses/` | 创建课程 |
| **计划** | POST | `/api/plans/generate` | 生成备考计划 |
| | POST | `/api/plans/detail` | 生成详细计划 |
| | POST | `/api/plans/generate_from_answers` | 根据诊断生成计划 |
| **复习** | - | `/api/review/*` | 闪卡复习相关 |
| **文献** | - | `/api/papers/*` | 文献管理相关 |
| **图片** | - | `/api/images/*` | 图片处理相关 |

完整 API 文档请在启动后端后访问：http://localhost:8000/docs

## 💾 数据存储

### 数据库

StudyMate 使用 SQLite 作为默认数据库，数据库文件位置：

- **开发模式**：`backend/data/studymate.db`
- **生产模式**：用户数据目录下的 StudyMate 文件夹

### 本地数据

- AI 配置（API Key、模型选择等）存储在浏览器 `localStorage`
- 主题设置、界面偏好等存储在浏览器 `localStorage`
- 笔记、课程、闪卡等核心数据存储在 SQLite 数据库

## 🤝 贡献指南

我们欢迎任何形式的贡献！如果你想为 StudyMate 做出贡献，请遵循以下步骤：

1. **Fork 本仓库**
   - 点击页面右上角的 Fork 按钮

2. **创建功能分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **提交你的更改**
   ```bash
   git commit -m 'Add some feature'
   ```

4. **推送到分支**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **发起 Pull Request**
   - 在 GitHub 上创建 Pull Request
   - 详细描述你的改动和原因

### 代码规范

- 前端遵循 Vue 3 官方风格指南
- 后端遵循 PEP 8 Python 编码规范
- 提交信息使用清晰的描述性语言

## 📄 许可证

本项目采用 [MIT License](LICENSE) 许可证，你可以自由使用、修改和分发。

## ❓ 常见问题

### Q: 启动后提示后端连接失败？

A: 请确认后端服务已启动（端口 8000），可以访问 http://localhost:8000/docs 检查后端是否正常运行。

### Q: AI 功能无法使用？

A: 请在设置中配置你的 AI API Key，确保模型名称和 Base URL 正确。可以使用「测试连接」按钮验证配置。

### Q: 数据会上传到云端吗？

A: 不会。StudyMate 的所有数据都存储在本地，包括笔记、课程、闪卡等。AI 请求会直接从你的设备发送到你配置的 API 服务商。

### Q: 如何备份数据？

A: 复制 `backend/data/studymate.db` 文件到安全位置即可。恢复时替换该文件。

### Q: 支持哪些平台？

A: Web 版本支持所有现代浏览器（Chrome、Edge、Firefox、Safari）。桌面应用目前提供 Windows 版本，macOS 和 Linux 可自行构建。

## 📞 联系与支持

- **GitHub Issues**：[提交问题或建议](https://github.com/August-Horton/studymate/issues)
- **功能需求**：欢迎通过 Issue 提出新功能建议
- **Bug 反馈**：请详细描述问题的复现步骤

---

<div align="center">

**如果这个项目对你有帮助，欢迎给个 ⭐ Star 支持一下！**

Made with ❤️ by StudyMate Team

</div>
