# Bottun Chatbot

这是一个包含前端（React + Vite）和后端（Python + Flask/FastAPI）的智能对话机器人系统。

## 项目结构

- `frontend/`: 前端代码，使用 React, TypeScript, Tailwind CSS 和 Vite 构建。
- `backend/`: 后端代码，使用 Python 编写。
- `config/`: 配置文件目录。
- `docs/`: 项目文档，包括 PRD 和技术架构。

## 部署步骤

### 1. 后端部署

1. 进入后端目录：
   ```bash
   cd backend
   ```
2. 创建虚拟环境（可选）：
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # macOS/Linux
   # 或 venv\Scripts\activate  # Windows
   ```
3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
4. 运行后端服务：
   ```bash
   python3 main.py
   ```

### 2. 前端部署

1. 进入前端目录：
   ```bash
   cd frontend
   ```
2. 安装依赖：
   ```bash
   npm install
   ```
3. 启动开发服务器：
   ```bash
   npm run dev
   ```
4. 构建生产版本：
   ```bash
   npm run build
   ```

## Git 仓库关联

如果您需要手动关联远程仓库：

```bash
git init
git remote add origin https://github.com/Sophiaaaa/bottun-chatbot.git
git add .
git commit -m "initial commit"
git push -u origin main
```
