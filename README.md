# Recipe App

个人菜谱管理应用 — 记录每一道美味，分享生活的味道。

支持菜谱的创建、编辑、搜索、分类筛选和一键分享为图片。

## 功能特性

- 菜谱管理：创建 / 编辑 / 删除，支持多图片上传与排序
- 食材清单：按分类管理食材，自动计算卡路里
- 标签筛选：多维度标签分类（菜系、口味、场景、烹饪方式、难度）
- 全文搜索：基于 MeiliSearch 的模糊搜索，支持同义词
- 分享图片：一键生成精美菜谱长图，可直接保存发送
- 管理后台：食材、标签、分类的增删改查，数据导入导出
- 响应式布局：适配桌面端和移动端

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite 7 + Tailwind CSS 4 + Pinia + Naive UI |
| 后端 | Python 3.11+ / FastAPI + SQLAlchemy (async) + Alembic |
| 数据库 | PostgreSQL 16 |
| 搜索引擎 | MeiliSearch 1.6 |
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
│   ├── scripts/            # 工具脚本 (seed.py 数据导入)
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml      # 生产部署编排
├── docker-compose.dev.yml  # 开发环境 (仅 PostgreSQL + MeiliSearch)
├── setup.sh                # 一键搭建开发环境
├── .env.example            # 环境变量模板
└── .gitignore
```

## 快速开始

### 一键搭建开发环境

```bash
# 自动安装依赖、启动数据库容器、配置环境
bash setup.sh
```

脚本会自动检测并安装 Node.js、Python 3.11+、Docker，启动 PostgreSQL 和 MeiliSearch 容器，安装前后端依赖。

### 手动搭建

**1. 启动依赖服务**

```bash
cp .env.example .env
# 按需修改 .env 中的数据库密码、密钥等

docker compose -f docker-compose.dev.yml up -d
```

**2. 启动后端**

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

后端运行在 `http://localhost:8000`，API 文档：`http://localhost:8000/docs`

**3. 启动前端**

```bash
cd frontend
npm install
npm run dev
```

前端运行在 `http://localhost:5173`，自动代理 API 请求到后端。

**4. 导入示例数据（可选）**

```bash
cd backend
source venv/bin/activate
python scripts/seed.py
```

## 生产部署

### Docker Compose 一键部署（推荐）

```bash
# 配置环境变量
cp .env.example .env
# 编辑 .env，务必修改以下配置：
#   POSTGRES_PASSWORD  — 数据库密码
#   SECRET_KEY         — JWT 密钥
#   ADMIN_PASSWORD     — 管理后台密码
#   MEILI_MASTER_KEY   — 搜索引擎密钥

# 构建并启动全部服务
docker compose up -d --build
```

启动后访问 `http://<服务器IP>` 即可使用（默认端口 80，可通过 `FRONTEND_PORT` 修改）。

**架构示意：**

```
用户 → Nginx(:80) ─┬─ 静态文件 (Vue SPA)
                    ├─ /api/*    → FastAPI(:8000)
                    └─ /uploads/* → FastAPI(:8000)
                                       │
                            ┌──────────┼──────────┐
                            ▼          ▼          ▼
                       PostgreSQL  MeiliSearch  uploads/
```

### 环境变量说明

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `POSTGRES_USER` | 数据库用户名 | `recipe_user` |
| `POSTGRES_PASSWORD` | 数据库密码 | `recipe_secret` |
| `POSTGRES_DB` | 数据库名 | `recipe_db` |
| `SECRET_KEY` | JWT 签名密钥 | `change-me-to-a-random-string` |
| `ADMIN_USERNAME` | 管理后台用户名 | `admin` |
| `ADMIN_PASSWORD` | 管理后台密码 | `admin123` |
| `MEILI_MASTER_KEY` | MeiliSearch 密钥 | `recipe_meili_master_key` |
| `FRONTEND_PORT` | 前端对外端口 | `80` |

> 生产环境请务必修改所有默认密码和密钥。

## License

Private project.
