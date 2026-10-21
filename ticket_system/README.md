# 工单 / 报修管理系统（Ticket System）

面向企业内部的报修工单系统：员工提交工单，处理人接单与流转，管理员查看统计与用户管理。服务端渲染 + Bootstrap 5，后台统计用 Chart.js。

## 技术栈

- Python 3.12 + Django 5.2
- MySQL 8（本地开发可回退 SQLite）
- Redis（缓存 + Celery Broker；无 Redis 时回退 LocMemCache，Celery 同步执行）
- Celery 异步任务（指派通知、状态变更邮件）
- Bootstrap 5 + Chart.js（CDN）
- pytest 风格 Django TestCase / 单元测试
- Docker Compose（web + Celery worker + MySQL + Redis + Nginx）

## 功能

- 登录 / 退出，账号由管理员在 Django Admin 创建
- 工单：创建、编辑、分类、优先级、关键词搜索、状态筛选、分页
- RBAC：员工 / 处理人 / 管理员三种角色
  - 员工：只能看自己提交的工单，未处理前可编辑
  - 处理人：查看全部工单，指派处理人，更新状态
  - 管理员：用户管理、改角色、禁用 / 启用账号
- 工单状态机：待处理 → 处理中 → 已解决 → 已关闭；拦截非法流转
- 评论、附件上传、流转记录
- Celery 异步发送指派通知与状态变更邮件
- Redis 缓存看板统计；MySQL 列表查询使用 `select_related` / `prefetch_related` 消除 N+1
- 统计看板：待处理 / 处理中 / 已解决 / 已关闭、近 7 天新建工单、平均解决时长

## 本地开发（SQLite + LocMemCache + Celery 同步）

```bash
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed
python manage.py runserver
```

- 访问：http://127.0.0.1:8000/
- Django Admin：http://127.0.0.1:8000/admin/
- 演示账号：
  - `admin / admin123`（管理员）
  - `agent / agent123`（处理人）
  - `employee / employee123`（员工）

本地没有 Redis 时，Celery 自动使用 eager 模式（任务同步执行），通知邮件打印到控制台。

## Docker Compose（MySQL + Redis + Celery worker + Nginx）

```bash
docker compose up --build
docker compose exec web python manage.py seed
```

- 通过 Nginx 访问：http://127.0.0.1/
- 直连 Web：http://127.0.0.1:8000/
- Celery worker 在独立容器中运行，使用 Redis 作为 Broker。

## 测试

```bash
python manage.py test
```

测试使用 SQLite 内存数据库、LocMemCache 和 eager Celery，不依赖外部服务。

## 目录

```text
config/
  settings.py       环境配置（MySQL/SQLite、Redis、Celery）
  urls.py           路由与 403/404
  celery.py         Celery 应用
tickets/
  models.py         6 张核心表 + 用户角色信号
  views.py          列表、详情、创建、编辑、指派、状态流转、看板、用户管理
  forms.py          ModelForm / 表单
  permissions.py    角色与状态机权限
  tasks.py          Celery 异步通知
  urls.py           15 条路由
  tests.py          13 项测试
  management/commands/seed.py
templates/tickets/  9 个页面模板
nginx/nginx.conf    反向代理 + 静态/媒体文件
```

## 核心表

`tickets_userprofile`、`tickets_category`、`tickets_ticket`、`tickets_comment`、`tickets_attachment`、`tickets_statuslog`

## 页面 / 路由

登录、退出、工单列表、工单详情、新建工单、编辑工单、指派、状态更新、评论、附件上传、统计看板、用户管理、角色修改、启用/禁用、健康检查，共 15 条路由。
