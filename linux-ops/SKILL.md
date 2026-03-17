---
name: linux-ops
description: "Advanced Linux server management skill for AI Agents. Supports multi-server SSH execution, encrypted configuration, command blacklisting, and execution confirmation."
---

# Linux Ops Skill

This skill allows Claude to manage multiple Linux servers via SSH. It is designed for secure and efficient server operations, including troubleshooting, health checks, and log retrieval.

## Features

- **Multi-Server Management**: Store and manage configurations for multiple servers.
- **Secure Authentication**: Supports SSH keys and encrypted password storage.
- **Safety First**: Built-in command blacklisting (e.g., `rm -rf /`) and confirmation requirements for sensitive commands.
- **Execution Feedback**: Returns stdout, stderr, and exit codes for precise error handling.

## Usage

### 1. Server Management

Before executing commands, you must add servers to the configuration.

**Add a server:**
```bash
python linux-ops/scripts/ssh_manager.py add-server <alias> <hostname> --user <username> --password <password> [--port <port>]
# OR with SSH key
python linux-ops/scripts/ssh_manager.py add-server <alias> <hostname> --user <username> --key <path_to_private_key>
```

**List servers:**
```bash
python linux-ops/scripts/ssh_manager.py list-servers
```

**Remove a server:**
```bash
python linux-ops/scripts/ssh_manager.py remove-server <alias>
```

### 2. Executing Commands

Execute a command on a specific server using its alias.

```bash
python linux-ops/scripts/ssh_manager.py exec <alias> "<command>"
```

**Example:**
```bash
python linux-ops/scripts/ssh_manager.py exec web-01 "uptime"
```

**Handling Confirmation:**
Some commands (e.g., `reboot`, `systemctl restart`) require confirmation. If a command fails with a "requires confirmation" message, retry with `--confirm`:

```bash
python linux-ops/scripts/ssh_manager.py exec db-01 "systemctl restart mysql" --confirm
```

### 3. Quick Diagnosis

Run a comprehensive health check (CPU, Memory, Disk, dmesg) on a server:

```bash
python linux-ops/scripts/ssh_manager.py diagnose <alias>
```

### 4. Safety Mechanisms

- **Blacklist**: Commands matching patterns in `linux-ops/scripts/blacklist.json` (e.g., `rm -rf /`, `mkfs`) are strictly blocked.
- **Confirmation**: Commands like `reboot`, `shutdown` require the `--confirm` flag.

## Best Practices

- Always check the exit code (`result['exit_code']`) to verify command success.
- Use aliases (e.g., `web-prod`, `db-staging`) that clearly identify the server's role.
- For complex troubleshooting, chain commands or use scripts, but be mindful of the blacklist.
