# Spring Cloud 微服务测试项目

用于 `app-deploy-ops` 部署测试的 Spring Cloud 微服务项目。

## 架构

```
Nginx (反向代理 + 负载均衡)
├── /api/user/*    → user-service:8081
├── /api/order/*   → order-service:8082
└── /api/pay/*     → pay-service:8083

服务注册与发现: Nacos
服务间调用: OpenFeign
消息队列: RabbitMQ
数据库: MySQL 8.0
缓存: Redis 7
```

## 模块说明

| 模块 | 端口 | 说明 | 外部依赖 |
|------|------|------|----------|
| `common` | - | 共享 DTO + API 接口 | 无 |
| `user-service` | 8081 | 用户 CRUD | MySQL, Redis, Nacos |
| `order-service` | 8082 | 订单 + 调用 user/pay | MySQL, Redis, Nacos, RabbitMQ, Feign |
| `pay-service` | 8083 | 支付记录 | MySQL, Redis, Nacos |

## 技术栈

| 技术 | 版本 |
|------|------|
| Spring Boot | 3.2.5 |
| Spring Cloud | 2023.0.1 |
| Spring Cloud Alibaba | 2023.0.1.3 |
| Java | 17 |
| Maven | >=3.6 |
| MyBatis-Plus | 3.5.9 |
| Nacos | 2.2.3 (容器化) |
| RabbitMQ | 3-management (容器化) |
| MySQL | 8.0 (容器化) |
| Redis | 7 (容器化) |

## 构建产物

- 构建命令: `mvn clean package -DskipTests` (父 POM)
- 产物列表:

| 模块 | JAR 路径 |
|------|----------|
| user-service | `user-service/target/user-service-1.0.0-SNAPSHOT.jar` |
| order-service | `order-service/target/order-service-1.0.0-SNAPSHOT.jar` |
| pay-service | `pay-service/target/pay-service-1.0.0-SNAPSHOT.jar` |

## 部署配置 (app-deploy-ops)

### 预设

使用 `spring-cloud-vue` 预设，此预设定义:

| 预设项 | 值 |
|--------|-----|
| 后端类型 | spring-boot (多服务) |
| 注册中心 | Nacos |
| 部署方式 | JAR + systemd |
| 中间件 | MySQL + Redis + Nacos + RabbitMQ |
| JVM 参数 | `-Xms256m -Xmx512m` |

### 服务部署目录

```
/opt/apps/{env}/backend/services/
├── user-service/app.jar
├── order-service/app.jar
└── pay-service/app.jar
```

### systemd 服务

每个服务有独立的 systemd 服务名:

| 服务名 | systemd service |
|--------|----------------|
| `user-service` | `user-service.service` |
| `order-service` | `order-service.service` |
| `pay-service` | `pay-service.service` |

### 构建命令

```bash
# 在项目根目录执行 (父 POM 会构建所有模块)
python scripts/deploy.py build \
  --env prod \
  --type backend \
  --source /path/to/test-project/springcloud-app
```

各个 JAR 位于各模块 `target/` 目录。

### Nginx 路由

| 路径 | 后端 | 端口 |
|------|------|------|
| `/api/user/*` | user-service | 8081 |
| `/api/order/*` | order-service | 8082 |
| `/api/pay/*` | pay-service | 8083 |

### API 端点

**user-service** (端口 8081):
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/users` | 用户列表 |
| GET | `/api/users/{id}` | 按 ID 查用户 |
| POST | `/api/users` | 创建用户 |
| GET | `/actuator/health` | 健康检查 |

**order-service** (端口 8082):
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/orders` | 订单列表 |
| GET | `/api/orders/{id}` | 按 ID 查订单 |
| POST | `/api/orders` | 创建订单 |
| POST | `/api/orders/{id}/pay` | 支付订单 |
| GET | `/actuator/health` | 健康检查 |

**pay-service** (端口 8083):
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/pays/order/{orderId}` | 按订单查支付 |
| POST | `/api/pays` | 创建支付 |
| GET | `/actuator/health` | 健康检查 |

### 服务间调用关系

```
order-service  ──Feign──→  user-service  (验证用户存在)
order-service  ──Feign──→  pay-service    (创建支付记录)
```

## SQL 初始化

启动前需初始化数据库:

```sql
CREATE DATABASE IF NOT EXISTS demo_db DEFAULT CHARSET utf8mb4;

USE demo_db;

CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(200),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    status INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pay_record (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_id BIGINT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    status INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

## 启动顺序

服务启动依赖 Nacos 就绪。推荐顺序:

1. MySQL → 2. Nacos → 3. RabbitMQ → 4. Redis → 5. user-service → 6. pay-service → 7. order-service

## 验证方式

```bash
# 验证每个服务健康状态
curl http://<server>:8081/actuator/health
curl http://<server>:8082/actuator/health
curl http://<server>:8083/actuator/health

# 通过 Nginx 验证完整链路
curl http://<server>/api/users
curl http://<server>/api/orders
curl http://<server>/api/pays/order/1
```

## 本地开发

```bash
cd springcloud-app
mvn clean compile
mvn clean package -DskipTests
```