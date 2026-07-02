# StudyMate 智学助手

一个基于 AI 的智能学习助手，支持笔记闪卡、论文润色和备考计划生成。

## 技术栈

- **前端**: Vue3 + Vant4（移动优先）
- **后端**: FastAPI + SQLite（轻量起动）
- **AI 层**: 预留接口，后续接入大模型

## 项目结构

```
studymate/
├── backend/              # FastAPI 后端
│   ├── main.py          # FastAPI 入口
│   ├── config.py        # 配置项
│   ├── database.py      # SQLite 连接与建表
│   ├── models.py        # SQLAlchemy 模型
│   ├── schemas.py       # Pydantic 请求/响应模型
│   ├── routers/         # API 路由
│   │   ├── notes.py     # 笔记上传、闪卡生成
│   │   ├── papers.py    # 论文润色与引文
│   │   └── plans.py     # 备考计划
│   ├── ai/              # AI 客户端
│   │   └── client.py    # 大模型调用（mock/真实）
│   └── requirements.txt
│
├── frontend/            # Vue3 前端
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.js
│   │   ├── router/index.js
│   │   ├── views/       # 页面组件
│   │   │   ├── Notes.vue
│   │   │   ├── Papers.vue
│   │   │   └── Plans.vue
│   │   └── api/         # axios 封装
│   │       └── index.js
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

## 快速开始

### 1. 启动后端

```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn main:app --reload
```

后端 API 文档自动出现在 http://localhost:8000/docs

### 2. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问 http://localhost:5173 即可看到三个 Tab 页面。

## 功能模块

### 笔记闪卡 (Notes)
- 上传文件或粘贴文本
- AI 自动整理笔记
- 生成闪卡（基于 SM-2 算法）
- 每日复习提醒

### 论文助手 (Papers)
- 论文文本润色
- 语法检查
- 表达优化（学术风格）
- 参考文献格式化

### 备考计划 (Plans)
- 输入课程和考试日期
- AI 生成个性化学习计划
- 每日任务分配
- 进度追踪

## 数据库表结构

- **users**: 用户信息
- **courses**: 课程信息
- **notes**: 笔记内容
- **flashcards**: 闪卡（含复习间隔、下次复习日期）
- **study_plans**: 学习计划

## 开发计划

- [x] 基础框架搭建
- [x] 数据库模型设计
- [x] API 接口实现
- [x] 前端页面开发
- [ ] 接入真实 AI API（DeepSeek/OpenAI）
- [ ] 实现 SM-2 复习算法
- [ ] 用户认证系统
- [ ] OCR 图片识别
- [ ] 语音转文字

## 环境变量

```bash
# .env
DATABASE_URL=sqlite:///./studymate.db
AI_API_KEY=your-deepseek-key
AI_BASE_URL=https://api.deepseek.com/v1
```

## License

MIT
