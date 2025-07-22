# TeleDL 前端管理后台

本项目基于 Vite + Vue3 + Element Plus，作为 TeleDL 后端的 HTTP 下载管理后台。

## 功能规划
- 下载任务列表（分页、状态筛选、刷新）
- 任务详情页
- 全局 axios 封装，后端 API 基地址为 `/api`

## 启动开发环境
```bash
npm run dev
```

## 生产构建
```bash
npm run build
```

## 依赖
- vue
- element-plus
- axios
- vite

## Docker 部署

1. 构建 Docker 镜像：
   ```bash
   docker build -t tele-frontend .
   ```

2. 启动容器：
   ```bash
   docker run -p 3000:3000 tele-frontend
   ```

## 注意事项

- 确保后端服务已启动并运行。
- 默认访问地址为 `http://localhost:3000`。

---
如需自定义主题或扩展页面，请参考 Element Plus 官方文档。
