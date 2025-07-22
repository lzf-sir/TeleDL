# TeleDL

## 项目简介

TeleDL 是一个基于前后端分离架构的 HTTP 下载管理工具，提供了任务管理、配置管理等功能。

## 项目结构

- `backend/`：后端服务，基于 Python 开发，提供 API 接口。
- `frontend/`：前端服务，基于 Vue3 开发，提供用户界面。
- `docker-compose.yml`：用于容器化部署的配置文件。

## 快速开始

### 本地运行

1. 启动后端服务：
   ```bash
   cd backend
   python main.py
   ```

2. 启动前端服务：
   ```bash
   cd frontend
   npm run dev
   ```

### Docker 部署

1. 构建并启动服务：
   ```bash
   docker-compose up --build
   ```

2. 访问服务：
   - 前端：`http://localhost:3000`
   - 后端：`http://localhost:8000`

## 注意事项

- 确保已安装 Docker 和 Docker Compose。
- 数据库默认使用 PostgreSQL，配置可在 `docker-compose.yml` 中修改。