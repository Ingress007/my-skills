---
name: linux-ops
description: "Linux server management skill for AI Agents. Reads SSH config for secure key-based authentication. Provides system diagnostics and command execution with safety controls."
---

# Linux Ops Skill

This skill allows Claude to manage Linux servers via SSH using your existing `.ssh/config` configuration.

## Features

- **SSH Config Integration**: Reads host configurations directly from your `.ssh/config` file.
- **Key-based Authentication**: Uses SSH keys for secure, passwordless authentication.
- **Safety First**: Built-in command blacklisting and confirmation requirements for sensitive commands.
- **System Diagnosis**: One-click health check for CPU, memory, disk, and system logs.
- **Execution Feedback**: Returns stdout, stderr, and exit codes for precise error handling.

## Prerequisites

Ensure your `.ssh/config` file contains the server configurations with SSH key authentication:

```
Host my-server
    HostName 192.168.1.10
    User root
    Port 22
    IdentityFile ~/.ssh/id_rsa
```

## Usage

### 1. List Servers

List all hosts configured in your `.ssh/config`:

```bash
python linux-ops/scripts/ssh_manager.py list-servers
```

### 2. Execute Commands

Execute a command on a server using its SSH config alias:

```bash
python linux-ops/scripts/ssh_manager.py exec <alias> "<command>"
```

**Example:**
```bash
python linux-ops/scripts/ssh_manager.py exec my-server "uptime"
```

**Handling Confirmation:**
Some commands (e.g., `reboot`, `systemctl restart`) require confirmation. If a command fails with a "requires confirmation" message, retry with `--confirm`:

```bash
python linux-ops/scripts/ssh_manager.py exec my-server "systemctl restart nginx" --confirm
```

### 3. System Diagnosis

Run a comprehensive health check (CPU, Memory, Disk, dmesg) on a server:

```bash
python linux-ops/scripts/ssh_manager.py diagnose <alias>
```

### 4. Safety Mechanisms

**Blacklisted (always blocked):**
- `rm -rf /`
- `mkfs`
- `dd if=`

**Requires `--confirm`:**
- `rm`
- `reboot`
- `shutdown`
- `systemctl stop/restart`

## Best Practices

- Always check the exit code (`result['exit_code']`) to verify command success.
- Use descriptive aliases in your `.ssh/config` (e.g., `web-prod`, `db-staging`) that clearly identify the server's role.
- Use the `diagnose` command for troubleshooting server issues.