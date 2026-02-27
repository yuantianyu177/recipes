# Recipe App

个人菜谱管理应用 — 记录每一道美味，分享生活的味道。

## 功能特性

- 菜谱管理：创建 / 编辑 / 删除，支持多图片上传
- 食材清单：按分类管理食材，自动计算卡路里
- 标签筛选：多维度标签分类
- 全文搜索：基于 MeiliSearch 的模糊搜索，支持同义词
- 分享图片：一键生成精美菜谱长图
- 管理后台：食材、标签、分类的增删改查，数据导入导出
- 响应式布局：全面适配桌面端和移动端

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite 7 + Tailwind CSS 4 + Pinia + Naive UI + TipTap 富文本 |
| 后端 | Python 3.11+ / FastAPI + SQLAlchemy (async) + Alembic + Pillow |
| 数据库 | PostgreSQL 16 |
| 搜索引擎 | MeiliSearch 1.6 |
| 图片处理 | Pillow + pillow-heif（HEIC/HEIF 支持） |
| 部署 | Docker Compose / Nginx |

## 项目结构

```
recipes/
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── api/            # API 请求封装
│   │   ├── components/     # 公共组件
│   │   ├── stores/         # Pinia 状态管理
│   │   └── views/          # 页面视图
│   ├── nginx.conf          # 生产环境 Nginx 配置
│   ├── Dockerfile
│   └── vite.config.js
├── backend/                # FastAPI 后端
│   ├── app/
│   │   ├── api/            # 路由 (recipes, tags, ingredients, upload, search)
│   │   ├── core/           # 配置、数据库、认证
│   │   ├── models/         # SQLAlchemy 模型
│   │   ├── schemas/        # Pydantic 模型
│   │   └── services/       # 业务逻辑 (搜索索引等)
│   ├── scripts/            # 工具脚本
│   ├── Dockerfile
└── requirements.txt
├── docker-compose.yml      # 生产部署编排
├── docker-compose.dev.yml  # 开发环境编排
├── .env.example            # 环境变量模板
└── .gitignore
```

## 开发

### 启动开发环境

```bash
# 启动所有服务（PostgreSQL + MeiliSearch + Backend + Frontend）
docker compose -f docker-compose.dev.yml up -d

# 访问应用
# 前端：http://localhost:5173
# 后端 API：http://localhost:8000
# API 文档：http://localhost:8000/docs
```

### 初始化数据（可选）

```bash
# 初始化测试数据（推荐）
docker compose -f docker-compose.dev.yml exec backend python scripts/init_db.py

# 清理数据库
docker compose -f docker-compose.dev.yml exec backend python scripts/reset_db.py
```

### 运行测试

```bash
docker compose -f docker-compose.dev.yml exec backend pytest
```

### 查看日志

```bash
# 查看所有服务日志
docker compose -f docker-compose.dev.yml logs -f

# 查看特定服务日志
docker compose -f docker-compose.dev.yml logs -f backend
docker compose -f docker-compose.dev.yml logs -f frontend
```

### 停止服务

```bash
docker compose -f docker-compose.dev.yml down
```

## 部署

### 1. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，**修改以下默认值**：

| 变量 | 说明 | 默认值（不安全） |
|------|------|-----------------|
| `POSTGRES_PASSWORD` | 数据库密码 | `recipe_secret` |
| `SECRET_KEY` | JWT 签名密钥 | `change-me-to-a-random-string` |
| `ADMIN_PASSWORD` | 管理后台密码 | `admin123` |
| `MEILI_MASTER_KEY` | 搜索引擎密钥 | `recipe_meili_master_key` |

其他可选配置：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `POSTGRES_USER` | 数据库用户名 | `recipe_user` |
| `POSTGRES_DB` | 数据库名 | `recipe_db` |
| `POSTGRES_HOST` | 数据库主机 | `localhost` |
| `POSTGRES_PORT` | 数据库端口 | `5432` |
| `ADMIN_USERNAME` | 管理后台用户名 | `admin` |
| `FRONTEND_PORT` | 外部访问端口 | `80` |
| `MEILI_HOST` | 搜索引擎地址 | `http://localhost:7700` |
| `UPLOAD_DIR` | 文件上传目录 | `./uploads` |

### 2. 启动所有服务

```bash
docker compose up -d --build
```

### 3. 初始化数据

```bash
# 初始化测试数据（推荐）
docker compose exec backend python scripts/init_db.py
```

启动后访问 `http://<服务器IP>` 即可使用。

### 架构示意

```
用户 → Nginx(:80) ─┬─ 静态文件 (Vue SPA)
                    ├─ /api/*    → FastAPI(:8000)
                    └─ /uploads/* → FastAPI(:8000)
                                       │
                            ┌──────────┼──────────┐
                            ▼          ▼          ▼
                       PostgreSQL  MeiliSearch  uploads/
```

## License

[MIT](LICENSE)
