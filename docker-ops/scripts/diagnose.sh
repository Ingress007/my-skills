#!/bin/bash
echo "=== DOCKER DIAGNOSIS ==="
echo "Date: $(date)"
echo "Hostname: $(hostname)"
echo ""

# Check if Docker is installed and running
echo "--- DOCKER STATUS ---"
if command -v docker &> /dev/null; then
    echo "Docker installed: $(docker --version)"
    if docker info &> /dev/null; then
        echo "Docker daemon: RUNNING"
    else
        echo "Docker daemon: NOT RUNNING"
        systemctl status docker --no-pager 2>/dev/null || service docker status 2>/dev/null
    fi
else
    echo "Docker: NOT INSTALLED"
fi
echo ""

# Docker Compose check
echo "--- DOCKER COMPOSE ---"
if command -v docker-compose &> /dev/null; then
    echo "docker-compose: $(docker-compose --version)"
elif docker compose version &> /dev/null; then
    echo "docker compose (plugin): $(docker compose version)"
else
    echo "Docker Compose: NOT INSTALLED"
fi
echo ""

# Container status
echo "--- CONTAINERS ---"
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "Unable to list containers"
echo ""

# Container stats (top 5 by CPU)
echo "--- CONTAINER STATS (TOP 5) ---"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" 2>/dev/null | head -n 6 || echo "Unable to get stats"
echo ""

# Images
echo "--- IMAGES ---"
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" 2>/dev/null | head -n 10 || echo "Unable to list images"
echo ""

# Disk usage
echo "--- DISK USAGE ---"
docker system df 2>/dev/null || echo "Unable to get disk usage"
echo ""

# Networks
echo "--- NETWORKS ---"
docker network ls --format "table {{.Name}}\t{{.Driver}}\t{{.Scope}}" 2>/dev/null || echo "Unable to list networks"
echo ""

# Volumes
echo "--- VOLUMES ---"
docker volume ls --format "table {{.Name}}\t{{.Driver}}" 2>/dev/null | head -n 10 || echo "Unable to list volumes"
echo ""

# Recent events (last 10)
echo "--- RECENT EVENTS (LAST 10) ---"
docker events --since 1h --until now --format "{{.Time}} {{.Type}} {{.Action}} {{.Actor}}" 2>/dev/null | head -n 10 || echo "No recent events"
echo ""

# Docker daemon logs (last 10 lines)
echo "--- DOCKER DAEMON LOGS (LAST 10) ---"
if [ -f /var/log/docker.log ]; then
    tail -n 10 /var/log/docker.log
elif journalctl -u docker --no-pager -n 10 &> /dev/null; then
    journalctl -u docker --no-pager -n 10
else
    echo "Docker logs not accessible"
fi
echo ""

echo "=== END DOCKER DIAGNOSIS ==="