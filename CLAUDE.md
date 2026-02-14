# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

个人菜谱管理应用，前后端分离架构。支持菜谱 CRUD、食材管理、标签筛选、MeiliSearch 全文搜索、一键生成分享图片。

## 技术栈

- **前端**: Vue 3 + Vite 7 + Tailwind CSS 4 + Pinia + Naive UI + TipTap 富文本编辑器
- **后端**: Python 3.11+ / FastAPI + SQLAlchemy (async, asyncpg) + Alembic
- **数据库**: PostgreSQL 16
- **搜索**: MeiliSearch 1.6
- **部署**: Docker Compose + Nginx 反向代理

## 常用命令

```bash
# 一键搭建开发环境（安装依赖 + 启动 PG/Meili 容器）
bash setup.sh

# 启动开发容器（仅 PostgreSQL + MeiliSearch）
docker compose -f docker-compose.dev.yml up -d

# 后端开发
cd backend && source venv/bin/activate
uvicorn app.main:app --reload          # http://localhost:8000, docs: /docs

# 前端开发
cd frontend && npm run dev             # http://localhost:5173, 代理 /api → :8000

# 前端构建
cd frontend && npm run build

# 导入示例数据
cd backend && source venv/bin/activate && python scripts/seed.py

# 后端测试
cd backend && source venv/bin/activate && pytest

# 生产部署
docker compose up -d --build
```

## 架构

```
Nginx(:80) → 静态文件 (Vue SPA)
           → /api/*     → FastAPI(:8000)
           → /uploads/* → FastAPI(:8000) 静态文件服务
                              ├── PostgreSQL (数据持久化)
                              └── MeiliSearch (全文搜索)
```

## 后端结构

- `app/main.py` — FastAPI 入口，注册所有路由和中间件
- `app/api/` — 路由模块: auth, recipes, tags, ingredients, search, upload, import_export, share
- `app/core/` — config（pydantic-settings）、database（async SQLAlchemy）、auth（JWT）
- `app/models/models.py` — 所有 SQLAlchemy ORM 模型集中定义
- `app/schemas/` — Pydantic 请求/响应模型
- `app/services/` — 业务逻辑（search 搜索索引、import_export 数据导入导出）
- `scripts/seed.py` — 示例数据导入脚本

## 前端结构

- `src/api/` — axios API 请求封装
- `src/components/` — 公共组件
- `src/stores/` — Pinia 状态管理
- `src/views/` — 页面视图
- Vite dev server 代理 `/api` 和 `/uploads` 到后端 :8000

## 关键约定

- 后端所有 API 路由前缀为 `/api`
- 文件上传存储在 `backend/uploads/`，通过 FastAPI StaticFiles 在 `/uploads` 路径提供服务
- 数据库连接使用 async（asyncpg），ORM 操作需 await
- 认证使用 JWT（python-jose），管理后台有独立的用户名/密码认证
