# linux-ops

Linux 服务器远程运维技能，通过 SSH 安全执行命令和系统诊断。

## 功能特性

| 特性 | 说明 |
|------|------|
| **SSH Config 集成** | 直接读取 `~/.ssh/config` 配置，无需额外存储 |
| **密钥认证** | 使用 SSH 密钥认证，安全无密码 |
| **命令安全机制** | 黑名单阻止危险命令，敏感命令需确认 |
| **系统诊断** | 一键获取服务器健康状态 |

## 安装

```bash
pip install paramiko
```

## 配置

确保 `~/.ssh/config` 配置了服务器：

```ssh
Host web-prod
    HostName 192.168.1.10
    User root
    Port 22
    IdentityFile ~/.ssh/id_rsa

Host db-staging
    HostName 192.168.1.20
    User admin
    Port 22
    IdentityFile ~/.ssh/id_rsa
```

## 使用方法

### 列出服务器

```bash
python linux-ops/scripts/ssh_manager.py list-servers
```

输出：
```json
{
  "hosts": ["web-prod", "db-staging"]
}
```

### 执行命令

```bash
python linux-ops/scripts/ssh_manager.py exec <alias> "<command>"
```

示例：
```bash
# 查看系统运行时间
python linux-ops/scripts/ssh_manager.py exec web-prod "uptime"

# 查看磁盘使用
python linux-ops/scripts/ssh_manager.py exec web-prod "df -h"

# 查看内存状态
python linux-ops/scripts/ssh_manager.py exec web-prod "free -m"
```

### 敏感命令确认

某些命令需要 `--confirm` 标志：

```bash
# 重启服务
python linux-ops/scripts/ssh_manager.py exec web-prod "systemctl restart nginx" --confirm

# 重启服务器
python linux-ops/scripts/ssh_manager.py exec web-prod "reboot" --confirm

# 删除文件
python linux-ops/scripts/ssh_manager.py exec web-prod "rm /tmp/oldfile" --confirm
```

### 系统诊断

```bash
python linux-ops/scripts/ssh_manager.py diagnose <alias>
```

诊断内容包括：
- 系统运行时间
- 磁盘使用情况
- 内存使用情况
- CPU 占用最高的进程
- 最近内核日志

## 安全机制

### 黑名单（完全阻止）

| 命令 | 说明 |
|------|------|
| `rm -rf /` | 删除根目录 |
| `mkfs` | 格式化磁盘 |
| `dd if=` | 磁盘镜像操作 |

### 需确认的命令

| 命令模式 | 说明 |
|----------|------|
| `rm` | 删除操作 |
| `reboot` | 重启系统 |
| `shutdown` | 关机 |
| `systemctl stop/restart` | 服务管理 |

### 自定义规则

编辑 `scripts/blacklist.json`：

```json
{
    "blacklist": [
        "^rm\\s+-rf\\s+/$",
        "^mkfs",
        "^dd\\s+if="
    ],
    "confirm_patterns": [
        "^rm",
        "^reboot",
        "^shutdown",
        "^systemctl\\s+(stop|restart)"
    ]
}
```

## API 返回格式

成功：
```json
{
  "status": "success",
  "stdout": "total 48\ndrwxr-xr-x  ...",
  "stderr": "",
  "exit_code": 0
}
```

失败：
```json
{
  "status": "error",
  "message": "Command blocked: Command matches blacklist pattern...",
  "exit_code": -1
}
```

## 测试

```bash
python linux-ops/test_skill.py
```

## 文件结构

```
linux-ops/
├── README.md               # 本文件
├── SKILL.md               # Claude Code Skill 定义
├── requirements.txt       # 依赖：paramiko
├── test_skill.py          # 测试套件
└── scripts/
    ├── ssh_manager.py     # CLI 入口
    ├── ssh_config_parser.py  # SSH config 解析
    ├── config_manager.py  # 配置和安全检查
    ├── blacklist.json     # 安全规则
    └── diagnose.sh        # 诊断脚本
```

## 许可证

MIT