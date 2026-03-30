# my-skills

Claude Code Skills 个人仓库，包含用于 AI Agent 的实用技能模块。

## 项目结构

```
my-skills/
├── .gitignore
└── linux-ops/                 # Linux 服务器运维 Skill
    ├── SKILL.md               # Skill 定义文档
    ├── requirements.txt       # Python 依赖
    ├── test_skill.py          # 测试套件
    └── scripts/
        ├── ssh_manager.py         # SSH 命令执行主程序
        ├── ssh_config_parser.py   # SSH config 解析器
        ├── config_manager.py      # 配置管理（黑名单检查）
        ├── blacklist.json         # 命令安全黑名单
        └── diagnose.sh            # 系统诊断脚本
```

---

## linux-ops

Linux 服务器远程运维技能，通过 SSH 安全执行命令。

### 特性

| 特性 | 说明 |
|------|------|
| **SSH Config 集成** | 直接读取 `~/.ssh/config` 配置，无需额外存储服务器信息 |
| **密钥认证** | 使用 SSH 密钥认证，无需存储密码 |
| **命令安全机制** | 黑名单阻止危险命令，敏感命令需确认 |
| **系统诊断** | 一键获取服务器健康状态 |

### 安装依赖

```bash
pip install -r linux-ops/requirements.txt
```

依赖：`paramiko`

### 配置 SSH

确保 `~/.ssh/config` 中配置了服务器：

```ssh
Host my-server
    HostName 192.168.1.10
    User root
    Port 22
    IdentityFile ~/.ssh/id_rsa
```

### 使用方法

```bash
# 列出 SSH config 中所有服务器
python linux-ops/scripts/ssh_manager.py list-servers

# 执行命令
python linux-ops/scripts/ssh_manager.py exec <alias> "<command>"

# 执行敏感命令（需确认）
python linux-ops/scripts/ssh_manager.py exec <alias> "reboot" --confirm

# 系统诊断
python linux-ops/scripts/ssh_manager.py diagnose <alias>
```

### 安全机制

**黑名单（完全阻止）：**
- `rm -rf /`
- `mkfs`
- `dd if=`

**需确认的命令：**
- `rm`
- `reboot`
- `shutdown`
- `systemctl stop/restart`

可在 `linux-ops/scripts/blacklist.json` 中自定义规则。

### 运行测试

```bash
python linux-ops/test_skill.py
```

### API 返回格式

成功：
```json
{
  "status": "success",
  "stdout": "...",
  "stderr": "...",
  "exit_code": 0
}
```

失败：
```json
{
  "status": "error",
  "message": "...",
  "exit_code": -1
}
```

---

## 许可证

MIT