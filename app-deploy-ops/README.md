# app-deploy-ops

Web 应用部署 Agent Skill — 本地控制端通过 SSH 远程操作服务器，完成应用部署。
支持 **单体**（Spring Boot + Vue）和 **微服务**（Spring Cloud + Vue）架构。

## 支持的架构

| 预设 | 架构 | 前端 | 后端 | 中间件容器 |
|------|------|------|------|-----------|
| `spring-boot-vue` | 单体 | Vue 3 + Vite | Spring Boot 单 JAR | MySQL, Redis |
| `spring-cloud-vue` | 微服务 | Vue 3 + Vite | Spring Cloud 多 JAR | MySQL, Redis, Nacos, RabbitMQ |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 SSH

确保 `~/.ssh/config` 配置了目标服务器连接：

```
Host my-server
    HostName 192.168.1.10
    User root
    Port 22
    IdentityFile ~/.ssh/id_rsa
```

### 3. 初始化环境

```bash
python scripts/deploy.py init \
  --server my-server \
  --env prod \
  --preset spring-boot-vue
```

### 4. 填写敏感配置

编辑 `~/.app-deploy-ops/secrets/prod/` 下的配置文件：

```
~/.app-deploy-ops/secrets/prod/
├── db-credentials.yaml       # 数据库密码（root_password, app_user, app_password）
├── redis-credentials.yaml    # Redis 密码
├── mq-credentials.yaml       # RabbitMQ 账号密码
├── app-secrets.yaml          # JWT Secret, API Key 等
└── ssl/                      # SSL 证书文件
```

### 5. 构建应用

```bash
# 前端
python scripts/deploy.py build \
  --env prod \
  --type frontend \
  --source /path/to/vue-project

# 后端（单体）
python scripts/deploy.py build \
  --env prod \
  --type backend \
  --source /path/to/springboot-project

# 后端（微服务多模块，在父 POM 目录执行）
python scripts/deploy.py build \
  --env prod \
  --type backend \
  --source /path/to/springcloud-project
```

### 6. 部署

**单体应用：**

```bash
python scripts/deploy.py deploy \
  --server my-server \
  --env prod \
  --preset spring-boot-vue \
  --backend-jar ./artifacts/app.jar \
  --frontend-dist ./artifacts/dist
```

**微服务：**

```bash
# 先准备多服务 JAR 目录
mkdir -p ./artifacts/services/{user-service,order-service,pay-service}
cp user-service/target/*.jar ./artifacts/services/user-service/app.jar
cp order-service/target/*.jar ./artifacts/services/order-service/app.jar
cp pay-service/target/*.jar ./artifacts/services/pay-service/app.jar

python scripts/deploy.py deploy \
  --server my-server \
  --env prod \
  --preset spring-cloud-vue \
  --backend-dir ./artifacts/services \
  --frontend-dist ./artifacts/dist
```

## 多服务目录约定

`--backend-dir` 指向的目录结构：

```
services/
├── user-service/
│   └── app.jar
├── order-service/
│   └── app.jar
└── pay-service/
    └── app.jar
```

子目录名必须与预设 `backend.services[].name` 一致。

## 命令参考

| 命令 | 功能 | 关键参数 |
|------|------|----------|
| `init` | 初始化环境 | `--server --env --preset` |
| `build` | 本地构建 | `--env --type frontend\|backend --source [--profile]` |
| `deploy` | 完整部署流程 | `--server --env --preset [--backend-jar\|--backend-dir] [--frontend-dist]` |
| `rollback` | 回滚到指定版本 | `--server --env --version [--service]` |
| `status` | 查看环境状态 | `--server --env [--preset]` |

## 部署流程

```
init → check_secrets → prepare_config (模板渲染)
→ SSH connect
→ 上传前端 dist
→ 上传 Nginx 配置 / application.yaml / systemd service
→ docker compose up (中间件)
→ 对每个服务: 备份旧 JAR → 上传新 JAR → 上传 application.yaml → systemd restart → 健康检查
→ 生成 deploy-manifest.json
```

## 服务器目录结构

```
/opt/apps/{env}/
├── frontend/vue-app/dist/        # Vue 静态资源
├── backend/services/
│   ├── user-service/app.jar      # 微服务 JAR
│   ├── order-service/app.jar
│   └── pay-service/app.jar
├── middleware/
│   ├── docker-compose.yaml       # 中间件编排
│   └── .env                      # 环境变量
├── config/                       # 共享配置
├── backup/app/                   # 应用包备份
└── data/                         # Docker 持久化数据
```

## 配置模板

使用 Jinja2 模板引擎，渲染时自动合并：
- **普通变量**：来自预设 `variables` 部分
- **结构化数据**：`nginx.routes`、`backend.services` 注入为 `nginx_routes`、`backend_services`
- **敏感变量**：从 `secrets/{env}/` 读取，优先级最高

## 安全说明

- 敏感配置独立存放于 `~/.app-deploy-ops/secrets/`，不入版本控制
- 部署前自动检测 secrets 完整性
- 服务器敏感文件权限 600，SSL 证书 400
- secrets/ 目录已加入 `.gitignore`

## 依赖

- paramiko — SSH 连接
- pyyaml — YAML 解析
- jinja2 — 模板渲染