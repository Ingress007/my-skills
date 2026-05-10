# linux-ops

Linux 服务器远程运维技能，通过 SSH 安全执行命令和系统诊断。

## 功能特性

| 特性 | 说明 |
|------|------|
| **SSH Config 集成** | 直接读取 `~/.ssh/config` 配置，无需额外存储 |
| **密钥认证** | 使用 SSH 密钥认证，安全无密码 |
| **服务器管理** | 一键添加/删除服务器，自动配置 SSH Key 认证 |
| **指纹验证** | 添加服务器时验证 host key 指纹，防止中间人攻击 |
| **命令安全机制** | 黑名单阻止危险命令，敏感命令需确认 |
| **系统诊断** | 一键获取服务器健康状态 |

## 安装

```bash
pip install paramiko
```

## 配置

### 方式一：自动配置（推荐）

使用 `server_manager.py` 自动添加服务器，会自动：
- 生成 SSH 密钥（如不存在）
- 上传公钥到服务器
- 配置 SSH config
- 验证 host key 指纹

```bash
python linux-ops/scripts/server_manager.py add my-server 192.168.1.10 --user root
```

### 方式二：手动配置

手动编辑 `~/.ssh/config`：

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

### 服务器管理

#### 添加服务器

```bash
# 交互式添加（需确认指纹）
python linux-ops/scripts/server_manager.py add <name> <ip> --port 22 --user root

# 自动接受指纹
python linux-ops/scripts/server_manager.py add my-server 192.168.1.100 -y
```

添加流程：
1. 获取服务器 SSH 指纹并显示
2. 用户确认指纹（防止中间人攻击）
3. 测试密码连接
4. 生成/检查本地 SSH Key
5. 上传公钥到服务器 authorized_keys
6. 写入 SSH config 配置
7. 验证 Key 认证是否生效

#### 删除服务器

```bash
python linux-ops/scripts/server_manager.py remove <name>
```

#### 列出服务器

```bash
python linux-ops/scripts/server_manager.py list
```

输出：
```json
{
  "status": "success",
  "config_path": "~/.ssh/config",
  "hosts": ["web-prod", "db-staging"],
  "count": 2
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

### 服务器添加安全流程

| 步骤 | 安全措施 |
|------|---------|
| 指纹获取 | 使用 Transport 直接获取，不验证 host key |
| 用户确认 | 交互式确认指纹，防止中间人攻击 |
| known_hosts | 用户确认后写入，后续连接可验证 |
| 公钥上传 | stdin 安全写入，避免命令注入 |
| 文件权限 | SSH config 和 known_hosts 设置 0o600 |

### 命令执行黑名单（完全阻止）

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
    ├── ssh_manager.py     # SSH 命令执行 CLI
    ├── server_manager.py  # 服务器添加/删除 CLI
    ├── config_manager.py  # 配置和安全检查
    ├── blacklist.json     # 安全规则
    └── diagnose.sh        # 诊断脚本
```

## 相关文件

服务器配置涉及的文件：

| 文件 | 路径 | 用途 |
|------|------|------|
| SSH config | `~/.ssh/config` | 服务器连接配置 |
| known_hosts | `~/.ssh/known_hosts` | 已验证的 host key |
| 私钥 | `~/.ssh/id_rsa` | SSH 私钥（无密码） |
| 公钥 | `~/.ssh/id_rsa.pub` | 上传到服务器的公钥 |

## 许可证

MIT