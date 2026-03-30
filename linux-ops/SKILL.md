---
name: linux-ops
description: "Linux server management skill for AI Agents. Reads SSH config for secure key-based authentication, with command blacklisting and execution confirmation."
---

# Linux Ops Skill

This skill allows Claude to manage Linux servers via SSH using your existing `.ssh/config` configuration. It is designed for secure and efficient server operations with SSH key authentication.

## Features

- **SSH Config Integration**: Reads host configurations directly from your `.ssh/config` file.
- **Key-based Authentication**: Uses SSH keys for secure, passwordless authentication.
- **Safety First**: Built-in command blacklisting (e.g., `rm -rf /`) and confirmation requirements for sensitive commands.
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

### 1. List Available Servers

List all hosts configured in your `.ssh/config`:

```bash
python linux-ops/scripts/ssh_manager.py list-servers
```

### 2. Executing Commands

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

### 3. Quick Diagnosis

Run a comprehensive health check (CPU, Memory, Disk, dmesg) on a server:

```bash
python linux-ops/scripts/ssh_manager.py diagnose <alias>
```

### 4. Safety Mechanisms

- **Blacklist**: Commands matching patterns in `linux-ops/scripts/blacklist.json` (e.g., `rm -rf /`, `mkfs`) are strictly blocked.
- **Confirmation**: Commands like `reboot`, `shutdown`, `rm`, `systemctl stop/restart` require the `--confirm` flag.

## Best Practices

- Always check the exit code (`result['exit_code']`) to verify command success.
- Use descriptive aliases in your `.ssh/config` (e.g., `web-prod`, `db-staging`) that clearly identify the server's role.
- For complex troubleshooting, chain commands or use scripts, but be mindful of the blacklist.
- Ensure SSH keys are properly configured with appropriate permissions on the target servers.