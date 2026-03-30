---
name: docker-ops
description: "Docker and Docker Compose management skill for AI Agents. Supports container lifecycle, image management, multi-registry operations, and Docker Compose deployments. Uses SSH config from linux-ops for secure connections."
---

# Docker Ops Skill

This skill provides Docker and Docker Compose management capabilities for AI Agents. It connects to remote servers via SSH using the shared SSH config from linux-ops.

## Features

- **Container Management**: Full lifecycle control (start/stop/restart/rm)
- **Image Management**: Pull, push, tag, remove images with multi-registry support
- **Docker Compose**: Deploy and manage multi-container applications
- **Network & Volume**: Create and manage Docker networks and volumes
- **Docker Diagnosis**: Comprehensive health check for Docker environments
- **Safety Controls**: Blacklist dangerous commands, require confirmation for sensitive operations

## Prerequisites

1. Install dependencies:
```bash
pip install -r docker-ops/requirements.txt
```

2. Ensure `~/.ssh/config` is configured with server connections (see linux-ops skill).

3. Docker must be installed on target servers.

## Usage

### Container Commands

```bash
# List containers
python docker-ops/scripts/docker_manager.py <alias> ps
python docker-ops/scripts/docker_manager.py <alias> ps --all

# View logs
python docker-ops/scripts/docker_manager.py <alias> logs <container> --lines 100

# Start/Stop/Restart (requires --confirm)
python docker-ops/scripts/docker_manager.py <alias> start <container> --confirm
python docker-ops/scripts/docker_manager.py <alias> stop <container> --confirm
python docker-ops/scripts/docker_manager.py <alias> restart <container> --confirm

# Remove container (requires --confirm)
python docker-ops/scripts/docker_manager.py <alias> rm <container> --confirm
python docker-ops/scripts/docker_manager.py <alias> rm <container> --force --volumes --confirm

# Execute command in container
python docker-ops/scripts/docker_manager.py <alias> exec <container> "ls /app"

# Resource stats
python docker-ops/scripts/docker_manager.py <alias> stats

# Inspect
python docker-ops/scripts/docker_manager.py <alias> inspect <container>
```

### Image Commands

```bash
# List images
python docker-ops/scripts/docker_manager.py <alias> images

# Pull image (supports custom registry)
python docker-ops/scripts/docker_manager.py <alias> pull nginx
python docker-ops/scripts/docker_manager.py <alias> pull my-image --registry registry.example.com

# Push image (requires --confirm)
python docker-ops/scripts/docker_manager.py <alias> push my-image --confirm

# Remove image (requires --confirm)
python docker-ops/scripts/docker_manager.py <alias> rmi my-image --confirm

# Registry login/logout
python docker-ops/scripts/docker_manager.py <alias> login registry.example.com
python docker-ops/scripts/docker_manager.py <alias> logout registry.example.com
```

### Docker Compose Commands

```bash
# List services
python docker-ops/scripts/docker_manager.py <alias> compose-ps --file compose.yaml

# Start services (requires --confirm)
python docker-ops/scripts/docker_manager.py <alias> compose-up --file compose.yaml --confirm
python docker-ops/scripts/docker_manager.py <alias> compose-up --file compose.yaml --build --confirm

# Stop services (requires --confirm)
python docker-ops/scripts/docker_manager.py <alias> compose-down --file compose.yaml --confirm
python docker-ops/scripts/docker_manager.py <alias> compose-down --file compose.yaml --volumes --confirm

# View logs
python docker-ops/scripts/docker_manager.py <alias> compose-logs --file compose.yaml --lines 100

# Pull images
python docker-ops/scripts/docker_manager.py <alias> compose-pull --file compose.yaml

# Restart services (requires --confirm)
python docker-ops/scripts/docker_manager.py <alias> compose-restart --file compose.yaml --confirm

# Build images (requires --confirm)
python docker-ops/scripts/docker_manager.py <alias> compose-build --file compose.yaml --confirm
```

### Docker Diagnosis

```bash
python docker-ops/scripts/docker_manager.py <alias> diagnose
```

Returns:
- Docker daemon status
- Container list and resource stats
- Image list
- Disk usage
- Networks and volumes
- Recent events
- Daemon logs

## Safety Mechanisms

**Blacklisted (always blocked):**
- `docker system prune -af`
- Batch removal commands with subshells

**Requires `--confirm`:**
- `docker stop/restart/rm/rmi/push/build`
- `docker compose up/down/restart/build`

## Configuration

Customize safety rules in `docker-ops/scripts/blacklist.json`:

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