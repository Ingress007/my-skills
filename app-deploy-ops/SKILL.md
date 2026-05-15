# app-deploy-ops Skill

## Description

应用部署 Agent Skill。本地控制端通过 SSH 远程操作服务器完成应用部署。
支持 Vue 前端 + Spring Boot / Spring Cloud 后端架构，兼容单服务与多服务（微服务）部署。

## When to use

- 用户需要部署 Vue + Spring Boot 单体应用（单 JAR）
- 用户需要部署 Spring Cloud 微服务应用（多 JAR）
- 用户需要在远程服务器上初始化 Java Web 运行环境
- 用户需要部署/回滚/查看应用状态
- 用户需要在服务器部署中间件（MySQL、Redis、Nacos、RabbitMQ）

## Presets

| 预设 | 前端 | 后端 | 中间件 | 服务模式 |
|------|------|------|--------|----------|
| `spring-boot-vue` | Vue 3 + Vite | Spring Boot | MySQL, Redis (容器) | 单服务 |
| `spring-cloud-vue` | Vue 3 + Vite | Spring Cloud 3 服务 | MySQL, Redis, Nacos, RabbitMQ (容器) | 多服务 |

## Workflow

```
1. init           → 创建工作空间 + secrets 目录
2. 填写 secrets   → 编辑 ~/.app-deploy-ops/secrets/{env}/ 下的敏感配置
3. build frontend → npm run build (本地)
4. build backend  → mvn package (本地)
5. deploy         → SSH → 备份 → 上传 JAR/dist → 中间件 up → 重启 → 健康检查
6. status         → 查看服务器 Docker + systemd 状态
7. rollback       → 从服务器备份恢复到指定版本
```

## CLI 命令

| 命令 | 功能 | 说明 |
|------|------|------|
| `init` | 初始化环境 | 创建工作空间、secrets 目录 |
| `build` | 本地构建 | `--type frontend\|backend` |
| `deploy` | 部署应用 | 支持 `--backend-jar` (单服务) / `--backend-dir` (多服务) |
| `rollback` | 回滚 | `--version` 指定备份时间戳 |
| `status` | 查看状态 | Docker 容器 + systemd 状态 |

### 部署示例

```bash
# 单体应用部署
python scripts/deploy.py deploy \
  --server my-server --env prod \
  --preset spring-boot-vue \
  --backend-jar ./artifacts/app.jar \
  --frontend-dist ./artifacts/dist

# 微服务部署（多 JAR）
python scripts/deploy.py deploy \
  --server my-server --env prod \
  --preset spring-cloud-vue \
  --backend-dir ./artifacts/services \
  --frontend-dist ./artifacts/dist

# 多服务目录结构要求:
# ./artifacts/services/
#   ├── user-service/app.jar
#   ├── order-service/app.jar
#   └── pay-service/app.jar
```

## Architecture Support

### 单体架构
```
Nginx (reverse proxy + static files)
  └── Spring Boot (JAR, systemd)
  └── MySQL + Redis (Docker Compose)
```

### 微服务架构
```
Nginx (reverse proxy + multi-route load balancing)
  ├── user-service:8081 (JAR, systemd)
  ├── order-service:8082 (JAR, systemd)
  └── pay-service:8083   (JAR, systemd)
  └── MySQL + Redis + Nacos + RabbitMQ (Docker Compose)
```

## Design Principles

1. **敏感配置独立** — 数据库密码、密钥等存于 `~/.app-deploy-ops/secrets/{env}/`，人为填写，不入版本控制
2. **模板驱动** — 所有配置通过 Jinja2 模板渲染，预设定义变量，secrets 注入敏感值
3. **单服务/多服务统一** — preset 中 `backend.services[]` 定义多服务，为空则视为单服务
4. **幂等部署** — 部署前自动备份旧版本，支持回滚
5. **健康检查** — systemd restart 后自动检测端口和 HTTP health endpoint

## Files

- `scripts/deploy.py` — CLI 主入口（init/build/deploy/rollback/status）
- `core/` — 核心逻辑（workspace, secret_manager, builder, deployer, backup, validator）
- `remote/` — SSH 远程操作（ssh, docker, systemd, file）
- `templates/` — Jinja2 配置模板（compose, nginx, systemd, java, env）
- `presets/` — YAML 预设配置（定义架构、服务、变量）
- `tests/` — 测试用例
- `test-project/` — 测试项目（vue3-app, springboot-app, springcloud-app）