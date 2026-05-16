# linux-ops 服务器管理功能测试报告

> **测试日期**: 2026-05-16
> **测试环境**: Windows 10 (26200) → WSL2 Ubuntu (`10.0.0.192:22`, user `root`)
> **测试工具**: `test_integration.py`（API 级集成测试）
> **测试主机名**: `wsl-ubuntu`

---

## 测试结果概览

| 总计 | 通过 | 失败 | 通过率 |
|------|------|------|--------|
| 59   | 59   | 0    | **100%** |

**退出码**: 0 · **耗时**: ~4.5s

---

## 测试项详情

### 1. SSH Key 设置 (2/2 ✓)

| 用例 | 结果 | 说明 |
|------|------|------|
| `ensure_key_exists()` | ✓ | 使用已有 `~/.ssh/id_ed25519` |
| 公钥内容有效 | ✓ | 返回 ed25519 公钥字符串非空 |

### 2. 服务器指纹获取 (5/5 ✓)

| 用例 | 结果 | 验证内容 |
|------|------|----------|
| 获取指纹 | ✓ | `ssh-ed25519 SHA256:1w/iPltYe1wSaTXULyHjBh4jk5hwm9CHMlRI5g40RZI` |
| 返回 `data` 字段 | ✓ | 包含 `host_key`、`key_type`、`fingerprint` |
| host_key 对象 | ✓ | paramiko PKey 实例 |
| 密钥类型 | ✓ | `ssh-ed25519` |
| SHA256 指纹 | ✓ | 64 字符 base64 |

### 3. 密码连接测试 (1/1 ✓)

| 用例 | 结果 | 响应 |
|------|------|------|
| `connect_with_password()` root@10.0.0.192:22 | ✓ | `connection_test_ok` |

### 4. SSH 公钥上传 (1/1 ✓)

| 用例 | 结果 | 说明 |
|------|------|------|
| `upload_ssh_key()` 上传 id_ed25519 公钥 | ✓ | 写入 `~/.ssh/authorized_keys`，自动去重 |

### 5. Key 认证验证 (2/2 ✓)

| 用例 | 结果 | 说明 |
|------|------|------|
| `test_key_auth()` 无密码连接 | ✓ | `key_auth_test_ok` |
| exit_code = 0 | ✓ | 命令执行成功 |

### 6. ServerManager API — 添加服务器 (12/12 ✓)

| 步骤 | 状态 | 说明 |
|------|------|------|
| name_check | success | 名称 `wsl-ubuntu` 可用 |
| password_connect | success | 密码连接成功 |
| ssh_key | success | 使用 `~/.ssh/id_ed25519` |
| upload_key | success | 公钥已上传至服务器 |
| write_config | success | 写入 `~/.ssh/config` |
| verify_key_auth | success | Key 认证验证通过 |
| `host_exists()` 验证 | ✓ | SSH config 中存在该主机 |
| hostname | ✓ | `10.0.0.192` |
| user | ✓ | `root` |
| identityfile | ✓ | `C:\Users\ingress\.ssh\id_ed25519` |

### 7. SSH 命令执行 (9/9 ✓)

| 命令 | 结果 | 关键输出 |
|------|------|----------|
| `uptime` | ✓ | `20:39:29 up 25 min, load average: 0.35, 0.16, 0.06` |
| `uname -a` | ✓ | `Linux ingress 6.6.114.1-microsoft-standard-WSL2 ... x86_64` |
| `df -h /` | ✓ | `/dev/sdd 1007G 1.9G 954G 1% /` |
| `free -m` | ✓ | `Mem: 15994 total, 672 used, 15321 avail` |
| `ls /root` | ✓ | 列出 root 目录 |
| `whoami` | ✓ | `root` |

### 8. 命令安全机制 (14/14 ✓)

#### 黑名单拦截（完全阻止）

| 命令 | 结果 | 错误信息 |
|------|------|----------|
| `rm -rf /` | ✓ blocked | `matches blacklist pattern: ^rm\s+-r` |
| `mkfs.ext4 /dev/sda1` | ✓ blocked | `matches blacklist pattern: ^mkfs` |
| `dd if=/dev/zero of=/dev/sda` | ✓ blocked | `matches blacklist pattern: ^dd\s+if` |

#### 确认拦截（需 `--confirm` 标志）

| 命令 | 无 `--confirm` | 说明 |
|------|---------------|------|
| `reboot` | ✓ blocked | `requires confirmation` |
| `systemctl restart sshd` | ✓ blocked | `requires confirmation` |
| `rm /tmp/test.txt` | ✓ blocked | `requires confirmation` |

#### 安全命令放行

| 命令 | 结果 | 说明 |
|------|------|------|
| `systemctl status sshd` | ✓ allowed | 不要求 confirm |
| 不存在的服务器 | ✓ error | `Host '__nonexistent__' not found` |

### 9. 系统诊断 (4/4 ✓)

| 检查项 | 结果 | 说明 |
|--------|------|------|
| 诊断脚本执行 | ✓ | exit_code=0, 2714 bytes |
| 内存信息 | ✓ | 输出含 Memory / Mem 相关段落 |
| CPU 信息 | ✓ | 输出含 CPU / load average |
| 磁盘信息 | ✓ | 输出含 Disk / Filesystem 信息 |

**样例输出摘要**（`diagnose.sh`）:

- Hostname: `ingress`
- Uptime: `20:39:22 up 25 min`
- 根分区: `/dev/sdd 1007G 1.9G 954G 1% /`

### 10. 列出服务器 (6/6 ✓)

| 用例 | 结果 | 说明 |
|------|------|------|
| `list_servers()` 返回 success | ✓ | |
| 包含 hosts/count 字段 | ✓ | |
| hosts 是列表类型 | ✓ | |
| count ≥ 1 | ✓ | 共 1 个主机 |
| `wsl-ubuntu` 在列表中 | ✓ | `['wsl-ubuntu']` |

### 11. 删除 & 重新添加服务器 (3/3 ✓)

| 操作 | 结果 | 说明 |
|------|------|------|
| `remove_server('wsl-ubuntu')` | ✓ | 从 SSH config 中删除 |
| `host_exists()` 验证 | ✓ | config 中已不存在 |
| `list_servers()` 验证 | ✓ | 列表不再包含 |
| 重新添加 | ✓ | 测试结束时自动恢复 `wsl-ubuntu` 条目 |

---

## 测试过程中发现并修复的问题

| # | 问题 | 根因 | 修复方式 |
|---|------|------|----------|
| 1 | WSL SSH 服务未安装 | WSL 默认不安装 openssh-server | `apt-get install openssh-server` |
| 2 | root 密码认证失败 | WSL root 无预设密码 / 配置密码错误 | 设置 root 密码；`test_integration.py` 中 `TEST_SERVER_PASSWORD` 与服务器一致 |
| 3 | `PermitRootLogin` 未启用 | 默认配置 `prohibit-password` | `sed -i` 修改 sshd_config |
| 4 | 测试脚本 KeyError on `result['stdout']` | error 结果不含 stdout key | 改为先检查 status 再访问 stdout |

---

## 最终状态

- `~/.ssh/config` 已添加 **`wsl-ubuntu`** 主机条目（测试 11 结束后已重新添加）
- 认证方式从密码升级为 **SSH Key（id_ed25519）**
- 服务器可通过别名直接操作：

```bash
# 执行命令
python linux-ops/scripts/ssh_manager.py exec wsl-ubuntu "uptime"

# 系统诊断
python linux-ops/scripts/ssh_manager.py diagnose wsl-ubuntu

# 列出所有服务器
python linux-ops/scripts/server_manager.py list
```

### 复现测试

```bash
cd linux-ops
python test_integration.py
```
