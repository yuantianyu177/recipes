# Recipe App - Frontend

基于 Vue 3 + Vite + Tailwind CSS 构建的菜谱管理前端应用。

## 技术栈

- **Vue 3** (Composition API + `<script setup>`)
- **Vite 7** (构建工具)
- **Tailwind CSS 4** (样式)
- **Pinia** (状态管理)
- **Vue Router** (路由)
- **Naive UI** (组件库)
- **TipTap** (富文本编辑器)

## 开发环境

### 前置条件

- Node.js 20+
- 后端服务运行在 `localhost:8000`（Vite 自动代理 `/api` 和 `/uploads`）

### 启动开发

```bash
# 安装依赖
npm install

# 启动开发服务器（默认 http://localhost:5173）
npm run dev
```

开发模式下 Vite 会自动将 `/api` 和 `/uploads` 请求代理到后端 `http://localhost:8000`。

## 部署

### 方式一：Docker Compose 一键部署（推荐）

在项目根目录执行：

```bash
# 复制并编辑环境变量
cp .env.example .env
# 编辑 .env 修改密码、密钥等配置

# 构建并启动所有服务
docker compose up -d --build
```

这会启动以下服务：
- **PostgreSQL** — 数据库
- **MeiliSearch** — 搜索引擎
- **Backend** — FastAPI 后端（端口 8000，内部通信）
- **Frontend** — Nginx 提供静态文件 + 反向代理（默认端口 80）

访问 `http://<服务器IP>` 即可使用。修改端口请编辑 `.env` 中的 `FRONTEND_PORT`。

### 方式二：手动构建部署

```bash
# 1. 构建前端静态文件
npm run build
```

构建产物在 `dist/` 目录，部署到任意 Web 服务器即可。

**Nginx 配置要点（参考 `nginx.conf`）：**

```nginx
server {
    listen 80;
    root /path/to/dist;
    index index.html;

    # SPA 路由回退
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        client_max_body_size 20M;
    }

    # 图片上传文件代理
    location /uploads/ {
        proxy_pass http://127.0.0.1:8000/uploads/;
    }
}
```

### 方式三：Docker 单独构建前端镜像

```bash
docker build -t recipe-frontend .
docker run -d -p 80:80 recipe-frontend
```

> 注意：单独运行前端容器时，需确保 Nginx 配置中的后端地址 (`backend:8000`) 改为实际后端地址。

## 项目结构

```
frontend/
├── src/
│   ├── api/            # API 请求封装
│   ├── components/     # 公共组件（布局、分享弹窗、编辑器等）
│   ├── stores/         # Pinia 状态管理
│   └── views/          # 页面视图
│       └── admin/      # 管理后台页面
├── nginx.conf          # 生产环境 Nginx 配置
├── Dockerfile          # 多阶段构建镜像
└── vite.config.js      # Vite 配置（含开发代理）
```
