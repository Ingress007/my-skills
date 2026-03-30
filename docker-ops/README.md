# docker-ops

Docker 和 Docker Compose 管理技能，支持容器生命周期、镜像管理、多仓库操作和 Docker Compose 部署。

## 功能特性

| 特性 | 说明 |
|------|------|
| **容器管理** | 完整生命周期控制（start/stop/restart/rm） |
| **镜像管理** | 拉取、推送、标签、删除镜像 |
| **Docker Compose** | 多容器应用部署和管理 |
| **多仓库支持** | 支持官方仓库和私有仓库 |
| **Docker 诊断** | 一键获取 Docker 环境健康状态 |
| **安全控制** | 黑名单和确认机制保护危险操作 |

## 安装

```bash
pip install paramiko
```

## 依赖

本 Skill 复用 `linux-ops` 的 SSH config 解析，需要确保：
1. 已配置 `~/.ssh/config`（参见 linux-ops 文档）
2. 目标服务器已安装 Docker

## 使用方法

### 容器管理

```bash
# 列出容器
python docker-ops/scripts/docker_manager.py <alias> ps
python docker-ops/scripts/docker_manager.py <alias> ps --all

# 查看日志
python docker-ops/scripts/docker_manager.py <alias> logs <container> --lines 100

# 启动/停止/重启（需确认）
python docker-ops/scripts/docker_manager.py <alias> start <container> --confirm
python docker-ops/scripts/docker_manager.py <alias> stop <container> --confirm
python docker-ops/scripts/docker_manager.py <alias> restart <container> --confirm

# 删除容器（需确认）
python docker-ops/scripts/docker_manager.py <alias> rm <container> --confirm
python docker-ops/scripts/docker_manager.py <alias> rm <container> --force --volumes --confirm

# 在容器中执行命令
python docker-ops/scripts/docker_manager.py <alias> exec <container> "ls /app"

# 资源监控
python docker-ops/scripts/docker_manager.py <alias> stats

# 查看详情
python docker-ops/scripts/docker_manager.py <alias> inspect <container>
```

### 镜像管理

```bash
# 列出镜像
python docker-ops/scripts/docker_manager.py <alias> images

# 拉取镜像（支持私有仓库）
python docker-ops/scripts/docker_manager.py <alias> pull nginx
python docker-ops/scripts/docker_manager.py <alias> pull my-image --registry registry.example.com

# 推送镜像（需确认）
python docker-ops/scripts/docker_manager.py <alias> push my-image --confirm
python docker-ops/scripts/docker_manager.py <alias> push my-image --registry registry.example.com --confirm

# 删除镜像（需确认）
python docker-ops/scripts/docker_manager.py <alias> rmi my-image --confirm

# 仓库登录/登出
python docker-ops/scripts/docker_manager.py <alias> login registry.example.com
python docker-ops/scripts/docker_manager.py <alias> logout registry.example.com
```

### Docker Compose 部署

```bash
# 查看服务状态
python docker-ops/scripts/docker_manager.py <alias> compose-ps --file compose.yaml

# 启动服务（需确认）
python docker-ops/scripts/docker_manager.py <alias> compose-up --file compose.yaml --confirm
python docker-ops/scripts/docker_manager.py <alias> compose-up --file compose.yaml --build --confirm

# 停止服务（需确认）
python docker-ops/scripts/docker_manager.py <alias> compose-down --file compose.yaml --confirm
python docker-ops/scripts/docker_manager.py <alias> compose-down --file compose.yaml --volumes --confirm

# 查看日志
python docker-ops/scripts/docker_manager.py <alias> compose-logs --file compose.yaml --lines 100

# 拉取镜像
python docker-ops/scripts/docker_manager.py <alias> compose-pull --file compose.yaml

# 重启服务（需确认）
python docker-ops/scripts/docker_manager.py <alias> compose-restart --file compose.yaml --confirm

# 构建镜像（需确认）
python docker-ops/scripts/docker_manager.py <alias> compose-build --file compose.yaml --confirm
```

### Docker 诊断

```bash
python docker-ops/scripts/docker_manager.py <alias> diagnose
```

诊断内容包括：
- Docker 安装状态和版本
- Docker Compose 安装状态
- Docker daemon 运行状态
- 容器列表和资源统计
- 镜像列表
- 磁盘使用情况
- 网络和卷列表
- 最近事件
- Docker daemon 日志

## 安全机制

### 黑名单（完全阻止）

| 命令 | 说明 |
|------|------|
| `docker system prune -af` | 强制清理所有资源 |
| 批量删除命令 | 使用子shell的批量删除 |

### 需确认的命令

| 命令模式 | 说明 |
|----------|------|
| `docker stop/restart/rm/rmi/push/build` | 容器/镜像操作 |
| `docker compose up/down/restart/build` | Compose 操作 |

### 自定义规则

编辑 `scripts/blacklist.json`：

```json
{
    "blacklist": [
        "^docker\\s+system\\s+prune\\s+-af"
    ],
    "confirm_patterns": [
        "^docker\\s+(stop|restart|rm|rmi|push|build)",
        "^docker\\s+compose\\s+(up|down|restart|build)"
    ]
}
```

## API 返回格式

成功：
```json
{
  "status": "success",
  "stdout": "CONTAINER ID   IMAGE   ...",
  "stderr": "",
  "exit_code": 0
}
```

失败：
```json
{
  "status": "error",
  "message": "Command requires confirmation: ...",
  "exit_code": -1
}
```

## 测试

```bash
python docker-ops/test_skill.py
```

## 文件结构

```
docker-ops/
├── README.md               # 本文件
├── SKILL.md               # Claude Code Skill 定义
├── requirements.txt       # 依赖：paramiko
├── test_skill.py          # 测试套件
└── scripts/
    ├── docker_manager.py  # CLI 入口
    ├── docker_commands.py # Docker 命令生成器
    ├── config_manager.py  # 配置和安全检查（复用 linux-ops SSH 解析）
    ├── blacklist.json     # 安全规则
    └── diagnose.sh        # Docker 诊断脚本
```

## 与 linux-ops 的关系

本 Skill 复用 `linux-ops` 的 SSH config 解析模块，实现共享服务器配置。两个 Skill 独立运行，职责分离：

- **linux-ops**: Linux 系统级操作
- **docker-ops**: Docker 容器级操作

## 许可证

MIT