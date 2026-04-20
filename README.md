# my-skills

Claude Code Skills 个人仓库，包含用于 AI Agent 的实用技能模块。

## Skills 概览

| Skill | 描述 | 主要功能 |
|-------|------|----------|
| [linux-ops](linux-ops/) | Linux 服务器运维 | SSH 执行、系统诊断、安全控制 |
| [docker-ops](docker-ops/) | Docker 容器管理 | 容器/镜像/Compose 管理、多仓库支持 |
| [rocketmq-ops](rocketmq-ops/) | RocketMQ 迁移管理 | Topic 导出/迁移/验证、系统过滤、配置对比 |

## 快速开始

### 1. 安装依赖

```bash
pip install paramiko
```

### 2. 配置 SSH

确保 `~/.ssh/config` 配置了服务器连接：

```ssh
Host my-server
    HostName 192.168.1.10
    User root
    Port 22
    IdentityFile ~/.ssh/id_rsa
```

### 3. 使用示例

**Linux 操作：**
```bash
python linux-ops/scripts/ssh_manager.py list-servers
python linux-ops/scripts/ssh_manager.py exec my-server "uptime"
```

**Docker 操作：**
```bash
python docker-ops/scripts/docker_manager.py my-server ps
python docker-ops/scripts/docker_manager.py my-server compose-up --file compose.yaml --confirm
```

**RocketMQ Topic 迁移：**
```bash
# 查看要迁移的 topic（dry-run）
python rocketmq-ops/scripts/rocketmq_topic_migration.py --source 源服务器 --target 目标服务器 --dry-run

# 执行迁移
python rocketmq-ops/scripts/rocketmq_topic_migration.py --source 源服务器 --target 目标服务器

# 核对验证
python rocketmq-ops/scripts/rocketmq_topic_verification.py --source 源服务器 --target 目标服务器 --detail
```

## 项目结构

```
my-skills/
├── README.md                   # 本文件
│
├── linux-ops/                  # Linux 基础操作 Skill
│   ├── README.md
│   ├── SKILL.md               # Claude Code Skill 定义
│   ├── requirements.txt       # 依赖：paramiko
│   ├── test_skill.py          # 测试套件
│   └── scripts/
│       ├── ssh_manager.py     # CLI 入口
│       ├── ssh_config_parser.py  # SSH config 解析
│       ├── config_manager.py  # 配置和安全检查
│       ├── blacklist.json     # 安全规则
│       └── diagnose.sh        # 诊断脚本
│
├── rocketmq-ops/               # RocketMQ 迁移 Skill
│   ├── README.md
│   ├── SKILL.md               # Claude Code Skill 定义
│   ├── requirements.txt       # 依赖：paramiko
│   └── scripts/
│       ├── rocketmq_topic_migration.py    # Topic 迁移脚本
│       └── rocketmq_topic_verification.py # Topic 核对脚本
│
└── docker-ops/                 # Docker 操作 Skill
    ├── README.md
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

## 测试

```bash
python linux-ops/test_skill.py
python docker-ops/test_skill.py
```

## 许可证

MIT