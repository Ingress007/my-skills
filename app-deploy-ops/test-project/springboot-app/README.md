# Spring Boot 单体测试项目

用于 `app-deploy-ops` 部署测试的 Spring Boot 单体后端项目。

## 技术栈

| 技术 | 版本 |
|------|------|
| Spring Boot | 3.2.5 |
| Java | 17 |
| Maven | >=3.6 |
| MyBatis-Plus | 3.5.9 |
| MySQL | 8.0 (容器化) |
| Redis | 7 (容器化) |

## 构建产物

- 构建命令: `mvn clean package -DskipTests`
- 产物: `target/demo-0.0.1-SNAPSHOT.jar`
- 部署方式: systemd 托管 JAR 进程

## 部署配置 (app-deploy-ops)

### 预设

使用 `spring-boot-vue` 预设，此预设定义:

- **单 JAR 部署**: JAR → `/opt/apps/{env}/backend/services/app/app.jar`
- **中间件**: MySQL 8.0 + Redis 7 (Docker Compose)
- **进程管理**: systemd, 服务名 `app`
- **JVM 参数**: `-Xms512m -Xmx1024m -XX:+UseG1GC`

### 构建命令

```bash
python scripts/deploy.py build \
  --env prod \
  --type backend \
  --source /path/to/test-project/springboot-app
```

### API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/users` | 用户列表 |
| GET | `/api/users/{id}` | 按 ID 查用户 |
| POST | `/api/users` | 创建用户 |
| GET | `/api/cache/{key}` | 读 Redis 缓存 |
| POST | `/api/cache/{key}` | 写 Redis 缓存(60s) |
| GET | `/actuator/health` | Spring Boot Actuator 健康检查 |

### SQL 初始化

应用启动前需在 MySQL 中创建 `demo_db` 数据库和 `users` 表:

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
```

### 数据库配置

项目 `application.yml` 中使用环境变量注入敏感配置:

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `MYSQL_PASSWORD` | `root` | MySQL root 密码 |
| `REDIS_HOST` | `localhost` | Redis 主机 |
| `REDIS_PORT` | `6379` | Redis 端口 |
| `REDIS_PASSWORD` | (空) | Redis 密码 |

部署时 `app-deploy-ops` 会将 secrets 中的值通过模板渲染写入 `application.yaml`。

## 验证方式

部署完成后检查:

```bash
curl http://<server>:8080/actuator/health
# 预期: {"status":"UP"}
```

## 本地开发

```bash
mvn clean compile
mvn clean package -DskipTests
java -jar target/demo-0.0.1-SNAPSHOT.jar
```