# 校园二手交易平台（Campus Marketplace）

面向校内学生的二手商品发布与交易后端，覆盖用户、商品、收藏、订单四条主链路，含管理员审核与 Redis 缓存。

## 技术栈

- Python 3.12 + FastAPI + Pydantic v2
- SQLAlchemy 2.0 + MySQL 8（本地开发可无缝回退 SQLite）
- Redis（缓存热点商品、空值缓存、互斥锁、浏览量计数；无 Redis 时自动回退内存缓存）
- JWT + RBAC（买家 / 卖家 / 管理员）
- Alembic 数据库迁移
- pytest + FastAPI TestClient
- Docker Compose（API + MySQL + Redis + Nginx）

## 功能

- 注册 / 登录 / 当前用户 / 买家升级卖家
- 商品发布、编辑、下架、删除，分类与关键词搜索，分页与价格排序
- 管理员审核商品（通过 / 驳回）、禁用 / 启用用户
- 收藏 / 取消收藏 / 收藏列表
- 订单：下单、卖家确认、买家完成、取消；状态机限制非法流转
- 商品详情浏览量 Redis 计数，每 10 次批量回写 MySQL
- 商品列表 / 详情缓存，空值缓存 + 互斥锁缓存击穿

## 本地开发（SQLite + 内存缓存，无需 MySQL/Redis）

```bash
python -m pip install -r requirements.txt
python seed.py
uvicorn app.main:app --reload
```

- API 文档：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/health
- 演示账号：`admin / admin123`，`seller / seller123`，`buyer / buyer123`

## Docker Compose（MySQL + Redis + Nginx）

```bash
docker compose up --build
docker compose exec api python seed.py
```

- 通过 Nginx 访问：http://127.0.0.1/docs
- 直连 API：http://127.0.0.1:8000/docs

## 测试

```bash
pytest -q
```

测试使用 SQLite 与内存缓存，不依赖外部服务。

## 目录

```text
app/
  main.py           FastAPI 入口
  config.py         环境配置
  database.py       SQLAlchemy engine / session
  models.py         6 张核心表
  schemas.py        Pydantic 请求 / 响应模型
  security.py       bcrypt + JWT
  deps.py           登录用户 / 角色权限依赖
  cache.py          Redis + 内存回退、互斥锁
  routers/
    auth.py         注册、登录、当前用户、升级卖家
    items.py        商品 CRUD、搜索、分页、浏览量
    categories.py   分类
    favorites.py    收藏
    orders.py       订单状态机
    admin.py        审核与用户管理
alembic/            数据库迁移
tests/              pytest 用例
nginx/nginx.conf    反向代理
```

## 核心表

`users`、`categories`、`items`、`item_images`、`favorites`、`orders`

## 接口

OpenAPI 共 22 个 path、27 个方法，覆盖：

- `/api/auth/*`
- `/api/categories`
- `/api/items`
- `/api/items/{id}/favorite`
- `/api/orders`
- `/api/admin/*`
