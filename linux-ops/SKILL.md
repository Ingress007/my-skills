---
name: linux-ops
description: "Linux server management skill for AI Agents. Reads SSH config for secure key-based authentication. Provides system diagnostics, server management, and command execution with safety controls."
---

# Linux Ops Skill

This skill allows Claude to manage Linux servers via SSH using your existing `.ssh/config` configuration.

## Features

- **SSH Config Integration**: Reads host configurations directly from your `.ssh/config` file.
- **Key-based Authentication**: Uses SSH keys for secure, passwordless authentication.
- **Server Management**: Add/remove servers with automatic SSH key setup and fingerprint verification.
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

Or use the server manager to auto-configure:

```bash
python linux-ops/scripts/server_manager.py add my-server 192.168.1.10 --user root
```

## Usage

### 1. Server Management

#### Add a new server

```bash
# Interactive (requires fingerprint confirmation)
python linux-ops/scripts/server_manager.py add <name> <ip> --port 22 --user root

# Auto-accept fingerprint
python linux-ops/scripts/server_manager.py add my-server 192.168.1.100 -y
```

The add process:
1. Retrieves server SSH fingerprint
2. Displays fingerprint for user confirmation (prevents MITM attacks)
3. Tests password connection
4. Generates/checks local SSH key
5. Uploads public key to server's authorized_keys
6. Writes SSH config entry
7. Verifies key-based authentication works

#### Remove a server

```bash
python linux-ops/scripts/server_manager.py remove <name>
```

#### List servers

```bash
python linux-ops/scripts/server_manager.py list
```

### 2. List Servers (ssh_manager)

List all hosts configured in your `.ssh/config`:

```bash
python linux-ops/scripts/ssh_manager.py list-servers
```

### 3. Execute Commands

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

### 4. System Diagnosis

Run a comprehensive health check (CPU, Memory, Disk, dmesg) on a server:

```bash
python linux-ops/scripts/ssh_manager.py diagnose <alias>
```

### 5. Safety Mechanisms

**Blacklisted (always blocked):**
- `rm -rf /`
- `mkfs`
- `dd if=`

**Requires `--confirm`:**
- `rm`
- `reboot`
- `shutdown`
- `systemctl stop/restart`

## Security Notes

- **Fingerprint Verification**: When adding a server, always verify the displayed fingerprint matches the server's actual fingerprint.
- **known_hosts**: Verified fingerprints are saved to `~/.ssh/known_hosts` for future connection validation.
- **File Permissions**: SSH config and known_hosts are set to 0o600 for security.

## Best Practices

- Always check the exit code (`result['exit_code']`) to verify command success.
- Use descriptive aliases in your `.ssh/config` (e.g., `web-prod`, `db-staging`) that clearly identify the server's role.
- Use the `diagnose` command for troubleshooting server issues.
- Use `server_manager.py` to add servers instead of manual configuration for better security.