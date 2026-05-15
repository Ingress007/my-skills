# app-deploy-ops 设计方案

应用部署 Agent Skill - 本地控制端通过 SSH 远程操作服务器，完成应用环境的初始化和部署。

---

## 一、核心定位

```
┌─────────────────────────────────────────────────────────────────┐
│                        本地电脑 (Control)                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  app-deploy-ops (Agent Skill)                            │   │
│  │  ├─ 工作空间管理 (workspace)                              │   │
│  │  ├─ 配置模板 (templates)                                  │   │
│  │  ├─ 构建工具 (nodejs/maven)                               │   │
│  │  └─ SSH 远程操作 (基于 shared/ssh_client.py)              │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ SSH
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       远程服务器 (Target)                        │
│  ├─ 中间件容器 (Docker Compose)                                 │   │
│  ├─ 应用运行时 (JDK/Nginx)                                      │   │
│  └─ 应用服务 (systemd)                                          │   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、技术栈覆盖

### 前端

| 组件 | 技术 | 部署方式 |
|------|------|----------|
| 框架 | Vue 3 + Vite | - |
| 构建 | Node.js (本地) | 检测已有/询问安装 |
| 托管 | Nginx | 服务器 systemd |

### 后端

| 组件 | 技术 | 版本管理 | 部署方式 |
|------|------|----------|----------|
| JDK | OpenJDK 8/11/17/21 | SDKMAN | 服务器宿主机 |
| 框架 | Spring Boot | - | JAR 包 |
| 构建 | Maven | 本地 | 检测已有/询问安装 |
| 进程管理 | systemd | - | 服务器宿主机 |

### 中间件（容器化）

| 组件 | 镜像 | 用途 |
|------|------|------|
| MySQL | mysql:8.0 | 主数据库 |
| Redis | redis:7 | 缓存/会话 |
| Nacos | nacos/nacos-server:v2.x | 注册/配置中心（微服务） |
| RabbitMQ | rabbitmq:3-management | 消息队列 |
| Elasticsearch | elasticsearch:8.x | 搜索引擎（可选） |
| MinIO | minio/minio | 对象存储（可选） |

---

## 三、部署架构

### 单体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        服务器                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                     Nginx                            │  │
│  │         (反向代理 + Vue 静态资源托管)                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                  │
│          ┌───────────────┼───────────────┐                │
│          ▼               ▼               ▼                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │ Spring Boot  │ │   MySQL      │ │    Redis     │      │
│  │   (JAR)      │ │  (容器)      │ │   (容器)     │      │
│  │  systemd     │ └──────────────┘ └──────────────┘      │
│  └──────────────┘                                          │
│         Docker Network: app-network                        │
└─────────────────────────────────────────────────────────────┘
```

### 微服务架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                            服务器                                    │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                         Nginx                                │    │
│  │              (反向代理 + Vue 静态资源 + 负载均衡)            │    │
│  └────────────────────────────────────────────────────────────┘    │
│                               │                                     │
│         ┌─────────────────────┼─────────────────────┐              │
│         ▼                     ▼                     ▼              │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐       │
│  │ user-service │     │ order-service│     │  pay-service │       │
│  │   (JAR)      │     │   (JAR)      │     │   (JAR)      │       │
│  └──────────────┘     └──────────────┘     └──────────────┘       │
│                               │                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Docker Compose (中间件)                    │  │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐                │  │
│  │  │ MySQL  │ │ Redis  │ │ Nacos  │ │RabbitMQ│                │  │
│  │  └────────┘ └────────┘ └────────┘ └────────┘                │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 四、操作模式

| 操作 | 执行位置 | 说明 |
|------|----------|------|
| 配置模板管理 | 本地 | 准备、渲染、存储配置模板 |
| 应用构建 | 本地 | Node.js/Vue 构建、Maven 打包 |
| 构建产物上传 | 本地 → 服务器 | SCP/SFTP 上传 JAR、dist 等 |
| 中间件部署 | 远程 SSH | Docker Compose 操作 |
| 应用部署 | 远程 SSH | systemd 服务管理 |
| 配置修改 | 远程 SSH | 修改前备份、修改后验证 |
| 备份管理 | 远程 SSH | 备份应用包、配置文件（仅服务器） |

---

## 五、构建工具策略

| 工具 | 策略 |
|------|------|
| Node.js | 默认使用本地已安装版本；如未安装，**先询问确认** 再安装 |
| Maven | 默认使用本地已安装版本；如未安装，**先询问确认** 再安装 |

### 检测逻辑

```python
# 检测构建工具是否已安装
def check_builder(builder_type):
    if builder_type == "nodejs":
        result = subprocess.run(["node", "--version"], capture_output=True)
        if result.returncode != 0:
            # 未安装，询问用户
            ask_user("Node.js 未检测到，是否需要安装？")
    
    elif builder_type == "maven":
        result = subprocess.run(["mvn", "--version"], capture_output=True)
        if result.returncode != 0:
            ask_user("Maven 未检测到，是否需要安装？")
```

---

## 六、敏感配置管理

### 设计原则

敏感配置（数据库账号密码、密钥、证书等）**独立存放、人为管理、不入模板**。

模板中仅使用变量占位符（如 `{{ db_password }}`），渲染时从 `secrets/` 目录读取实际值。

### 分类

| 类别 | 内容 | 存放位置 | 管理方式 |
|------|------|----------|----------|
| 数据库凭证 | root 密码、应用账号密码 | `secrets/db-credentials.yaml` | 人为填写 |
| Redis 凭证 | Redis 密码 | `secrets/redis-credentials.yaml` | 人为填写 |
| MQ 凭证 | RabbitMQ 账号密码 | `secrets/mq-credentials.yaml` | 人为填写 |
| SSL 证书 | 证书文件 + 私钥 | `secrets/ssl/` | 人为放置 |
| 应用密钥 | JWT Secret、API Key 等 | `secrets/app-secrets.yaml` | 人为填写 |
| SSH 密钥 | 远程部署私钥 | `~/.ssh/` | 人为管理 |

### 本地 secrets 目录

```
~/.app-deploy-ops/secrets/{env_name}/
├── db-credentials.yaml          # 数据库凭证
├── redis-credentials.yaml       # Redis 凭证
├── mq-credentials.yaml          # 消息队列凭证
├── app-secrets.yaml             # 应用密钥
└── ssl/                         # SSL 证书
│   ├── cert.pem
│   └── key.pem
```

### secrets 文件格式

```yaml
# secrets/{env}/db-credentials.yaml
mysql:
  root_password: ""              # 人为填写
  app_user: ""
  app_password: ""
  database: ""
```

```yaml
# secrets/{env}/redis-credentials.yaml
redis:
  password: ""                   # 人为填写
```

### 工作流程

```
1. 初始化环境时，生成 secrets/ 模板文件（值为空）
2. 用户人为填写 secrets/ 中的实际值
3. 部署时，渲染模板从 secrets/ 读取值，填充到配置文件
4. secrets/ 文件不进入版本控制（.gitignore）
5. 服务器上的敏感配置文件权限限制为 600
```

### 安全规则

- secrets/ 目录加入 `.gitignore`，**不入版本控制**
- 首次初始化时生成空模板，提示用户填写
- 部署前检测 secrets 是否已填写，**未填写则终止部署**
- 服务器敏感文件权限设置为 `600`，仅 owner 可读写
- 证书文件上传后设置 `400`，仅 owner 可读
- 模板渲染产物在工作空间中，部署完成后可清理

---

## 七、工作空间设计

### 本地工作空间

```
~/.app-deploy-ops/
├── workspaces/
│   └── {env_name}/                      # 环境工作空间
│       ├── {timestamp}/                 # 部署任务工作目录
│       │   ├── config/                  # 生成的配置文件（渲染后）
│       │   │   ├── docker-compose.yaml
│       │   │   ├── application.yaml
│       │   │   ├── nginx.conf
│       │   │   └── systemd/
│       │   │       └── app.service
│       │   ├── artifacts/               # 构建产物
│       │   │   ├── app.jar
│       │   │   └── dist/
│       │   ├── logs/                    # 部署日志
│       │   │   └── deploy.log
│       │   └── deploy-manifest.json     # 部署清单
│       │
│       └── current -> {timestamp}/      # 当前部署的软链接
│
├── templates/                           # 配置模板（不变）
│   ├── compose/
│   │   ├── middleware-springboot.yaml.j2
│   │   └── middleware-springcloud.yaml.j2
│   ├── nginx/
│   │   ├── app.conf.j2
│   │   └── ssl.conf.j2
│   ├── systemd/
│   │   └── spring-boot.service.j2
│   ├── java/
│   │   └── application.yaml.j2
│   └── env/
│       └── .env.j2
│
├── presets/                             # 预设配置
│   ├── spring-boot-vue.yaml
│   └── spring-cloud-vue.yaml
│
├── cache/
│   └── artifacts/                       # 构建缓存
│
├── secrets/                             # 敏感配置（人为管理）
│   └── {env_name}/
│       ├── db-credentials.yaml
│       ├── redis-credentials.yaml
│       ├── mq-credentials.yaml
│       ├── app-secrets.yaml
│       └── ssl/
│           ├── cert.pem
│           └── key.pem
│
└── config.yaml                          # 全局配置
```

### 服务器目录结构

```
/opt/apps/{env}/
├── frontend/
│   └── vue-app/
│       └── dist/
│
├── backend/
│   ├── services/
│   │   ├── user-service/
│   │   │   ├── app.jar
│   │   │   └── config/
│   │   └── order-service/
│   └── libs/
│
├── middleware/
│   ├── docker-compose.yaml
│   ├── .env
│   └── init/
│
├── backup/                              # 备份目录
│   ├── app/
│   │   ├── app.jar.2024-01-15_10-30-00.bak
│   │   └── app.jar.2024-01-16_14-20-00.bak
│   ├── config/
│   │   ├── application.yaml.2024-01-15_10-30-00.bak
│   │   └── nginx.conf.2024-01-15_10-30-00.bak
│   └── db/
│       └── mysql_backup_2024-01-15.sql.gz
│
├── logs/
│   ├── frontend/
│   ├── backend/
│   └── middleware/
│
├── data/                                # Docker 数据卷
│   ├── mysql/
│   ├── redis/
│   └── nacos/
│
└── config/
    ├── nginx/
    ├── systemd/
    └── secrets/                         # 敏感配置（权限 600）
        ├── db-credentials.yaml
        ├── redis-credentials.yaml
        └── ssl/
            ├── cert.pem                 # 权限 400
            └── key.pem                  # 权限 400
```

---

## 八、备份策略

| 类型 | 备份时机 | 备份位置 |
|------|----------|----------|
| 应用包 | 部署前 | **仅服务器** `/opt/apps/{env}/backup/app/` |
| 配置文件 | 修改前 | **仅服务器** `/opt/apps/{env}/backup/config/` |
| 数据库 | 定时/手动 | **仅服务器** `/opt/apps/{env}/backup/db/` |

### 备份命名规范

```
{filename}.{timestamp}.bak
# 例如: app.jar.2024-01-15_10-30-00.bak
```

---

## 九、配置模板管理

### 模板引擎

使用 **Jinja2** 模板引擎。

### 模板示例

```yaml
# templates/java/application.yaml.j2
spring:
  application:
    name: {{ app_name }}
  profiles:
    active: {{ env }}
  datasource:
    url: jdbc:mysql://{{ db_host }}:{{ db_port }}/{{ db_name }}?useSSL=false&serverTimezone=Asia/Shanghai
    username: {{ db_user }}
    password: {{ db_password }}
  redis:
    host: {{ redis_host }}
    port: {{ redis_port }}
    password: {{ redis_password }}
  {% if nacos_enabled %}
  cloud:
    nacos:
      discovery:
        server-addr: {{ nacos_host }}:{{ nacos_port }}
  {% endif %}

server:
  port: {{ app_port }}
```

### 变量来源

模板变量分为两类：

1. **普通变量** - 来自预设配置文件，如端口、服务名等非敏感信息
2. **敏感变量** - 来自 `secrets/` 目录，如密码、密钥等，人为填写

```yaml
# presets/spring-boot-vue.yaml
variables:
  # 普通变量（预设配置中直接定义）
  app_name: myapp
  env: prod
  db_host: 127.0.0.1
  db_port: 3306
  db_name: app_db
  app_port: 8080

# 敏感变量（从 secrets/ 读取，不在预设中定义）
# db_password → secrets/{env}/db-credentials.yaml → mysql.root_password
# redis_password → secrets/{env}/redis-credentials.yaml → redis.password
```

渲染时，敏感变量从对应 secrets 文件中自动提取，与普通变量合并后填充模板。

---

## 十、部署流程

```
1. 初始化工作空间
   └─→ 创建 ~/.app-deploy-ops/workspaces/{env}/{timestamp}/

2. 检测构建工具
   ├─→ 检测本地 Node.js / Maven
   └─→ 未安装则询问用户是否需要安装

3. 本地构建
   ├─→ 前端：npm run build → dist/
   └─→ 后端：mvn package → *.jar
   └─→ 构建产物保存到工作空间/artifacts/

4. 检查敏感配置
   ├─→ 检测 secrets/{env}/ 中各文件是否已填写
   ├─→ 未填写则终止部署，提示用户补充
   └─→ 已填写则继续

5. 准备配置文件
   ├─→ 合并普通变量 + 敏感变量
   ├─→ 渲染模板 → 工作空间/config/
   └─→ 不修改原模板文件

6. 连接服务器
   └─→ 通过 SSH config 读取服务器信息

7. 服务器备份
   ├─→ 备份应用包 → 服务器 /opt/apps/{env}/backup/app/
   └─→ 备份配置文件 → 服务器 /opt/apps/{env}/backup/config/

8. 上传新版本
   ├─→ 上传 JAR 包
   ├─→ 上传 dist/
   ├─→ 上传配置文件
   └─→ 上传敏感配置（权限设置 600/400）

9. 部署中间件
   └─→ docker-compose up -d

10. 重启应用服务
    └─→ systemctl restart {service}

11. 健康检查
    ├─→ 检查进程状态
    ├─→ 检查端口监听
    └─→ HTTP 健康检查

12. 生成部署清单
    └─→ deploy-manifest.json
```

---

## 十一、预设配置

### 单体架构预设

```yaml
# presets/spring-boot-vue.yaml
name: spring-boot-vue
description: Java 单体应用 + Vue 前端

architecture:
  type: spring-boot

frontend:
  framework: vue
  build_tool: vite
  deploy:
    type: nginx-static

backend:
  framework: spring-boot
  deploy:
    type: jar
    process_manager: systemd

middleware:
  containers:
    - name: mysql
      image: mysql:8.0
      essential: true
    - name: redis
      image: redis:7
      essential: true

java:
  version: 17
  provider: sdkman

nginx:
  upstream:
    - name: backend
      servers:
        - 127.0.0.1:8080
```

### 微服务架构预设

```yaml
# presets/spring-cloud-vue.yaml
name: spring-cloud-vue
description: Java 微服务架构 + Vue 前端

architecture:
  type: spring-cloud

frontend:
  framework: vue
  deploy:
    type: nginx-static

backend:
  framework: spring-boot
  registry: nacos
  deploy:
    type: jar
  services:
    - name: user-service
      port: 8081
    - name: order-service
      port: 8082
    - name: pay-service
      port: 8083

middleware:
  containers:
    - name: mysql
      image: mysql:8.0
    - name: redis
      image: redis:7
    - name: nacos
      image: nacos/nacos-server:v2.2.3
    - name: rabbitmq
      image: rabbitmq:3-management

nginx:
  routes:
    - path: /api/user
      upstream: user-service
    - path: /api/order
      upstream: order-service
    - path: /api/pay
      upstream: pay-service
```

---

## 十二、核心命令

### 初始化环境

```bash
python scripts/deploy.py init \
  --server my-server \
  --env prod \
  --preset spring-boot-vue
```

### 构建应用

```bash
# 构建前端
python scripts/deploy.py build \
  --env prod \
  --type frontend \
  --source /path/to/vue-project

# 构建后端
python scripts/deploy.py build \
  --env prod \
  --type backend \
  --source /path/to/java-project \
  --profile prod
```

### 部署应用

```bash
# 完整部署
python scripts/deploy.py deploy \
  --server my-server \
  --env prod \
  --preset spring-boot-vue
```

### 备份管理

```bash
# 备份
python scripts/deploy.py backup \
  --server my-server \
  --env prod \
  --backup-app \
  --backup-config
```

### 回滚

```bash
python scripts/deploy.py rollback \
  --server my-server \
  --env prod \
  --version 2024-01-15_10-30-00
```

### 状态查看

```bash
python scripts/status.py --env prod
```

---

## 十三、部署清单

```json
{
  "deploy_id": "20240116_142000",
  "env": "prod",
  "server": "my-server",
  "preset": "spring-boot-vue",
  "timestamp": "2024-01-16T14:20:00Z",
  "status": "success",
  "artifacts": {
    "frontend": {
      "checksum": "sha256:abc123..."
    },
    "backend": {
      "checksum": "sha256:def456..."
    }
  },
  "backups": {
    "app": "/opt/apps/prod/backup/app/app.jar.2024-01-16_14-20-00.bak",
    "config": "/opt/apps/prod/backup/config/application.yaml.2024-01-16_14-20-00.bak"
  },
  "health_check": {
    "mysql": "healthy",
    "redis": "healthy",
    "app": "healthy"
  },
  "duration": "3m 42s"
}
```

---

## 十四、模块结构

```
app-deploy-ops/
├── README.md
├── SKILL.md
├── DESIGN.md                       # 本文档
├── requirements.txt
├── config.yaml
│
├── core/
│   ├── __init__.py
│   ├── workspace.py               # 工作空间管理
│   ├── secret_manager.py          # 敏感配置管理
│   ├── builder.py                 # 本地构建
│   ├── deployer.py                # 部署执行
│   ├── backup.py                  # 服务器备份管理
│   └── validator.py               # 验证检查
│
├── builders/
│   ├── __init__.py
│   ├── nodejs_builder.py          # Node.js 构建
│   └── maven_builder.py           # Maven 构建
│
├── remote/
│   ├── __init__.py
│   ├── ssh_ops.py                 # SSH 操作封装
│   ├── docker_ops.py              # Docker 操作
│   ├── systemd_ops.py             # Systemd 操作
│   ├── file_ops.py                # 远程文件操作
│   └── backup_ops.py              # 服务器备份操作
│
├── templates/
│   ├── compose/
│   ├── nginx/
│   ├── systemd/
│   ├── java/
│   └── env/
│
├── presets/
│   ├── spring-boot-vue.yaml
│   └── spring-cloud-vue.yaml
│
├── scripts/
│   ├── deploy.py
│   ├── rollback.py
│   └── status.py
│
└── tests/
    └── test_skill.py
```

---

## 十五、依赖模块

```
shared/
├── ssh_client.py          # SSH 连接封装
├── ssh_config_parser.py   # SSH config 解析
└── type_defs.py           # 类型定义
```

---

## 十六、安全考虑

| 安全项 | 措施 |
|--------|------|
| 敏感信息 | 独立存放于 secrets/ 目录，人为管理，不入模板和版本控制 |
| 敏感文件权限 | 服务器上凭证文件 600，证书文件 400，仅 owner 可读写 |
| secrets 审校 | 部署前自动检测 secrets 是否填写完整，未填写则终止 |
| 版本控制 | secrets/ 加入 .gitignore，绝不提交到 Git |
| SSH 连接 | 使用 SSH config，支持密钥认证 |
| 操作日志 | 记录所有 SSH 操作，便于审计 |
| 权限控制 | 应用以非 root 用户运行 |
| 渲染产物清理 | 工作空间中含敏感信息的渲染产物，部署完成后可选清理 |

---

## 十七、下一步

1. 实现 `core/workspace.py` - 工作空间管理
2. 实现 `core/secret_manager.py` - 敏感配置管理（模板生成、填写检测、变量合并）
3. 实现 `builders/` - 构建工具集成
4. 实现 `remote/` - SSH 远程操作
5. 编写配置模板 `templates/`
6. 实现 `scripts/deploy.py` - CLI 入口
7. 编写测试用例 `tests/test_skill.py`