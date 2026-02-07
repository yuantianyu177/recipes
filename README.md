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

## 开发

所有依赖服务（PostgreSQL、MeiliSearch）和代码（后端、前端）均预设了相同的默认配置，开发环境零配置即可运行。

### 一键启动

```bash
bash setup.sh
```

脚本会自动检测并安装 Node.js、Python 3.11+、Docker，启动数据库容器，安装前后端依赖。完成后按提示分别启动前后端即可。

```bash
# 启动后端
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# 运行在 http://localhost:8000，API 文档：http://localhost:8000/docs

# 启动前端
cd frontend
npm install
npm run dev
# 运行在 http://localhost:5173，自动代理 /api 和 /uploads 到后端

# 4. 导入示例数据（可选）
cd backend && source venv/bin/activate
python scripts/seed.py
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
| `ADMIN_USERNAME` | 管理后台用户名 | `admin` |
| `FRONTEND_PORT` | 外部访问端口 | `80` |

### 2. 构建并启动

```bash
docker compose up -d --build
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
