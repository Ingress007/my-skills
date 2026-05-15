"""Docker 操作 - 远程 Docker Compose 管理"""


class DockerManager:
    """远程 Docker 操作"""

    def __init__(self, ssh_client):
        self.ssh = ssh_client

    def check_docker(self) -> dict:
        """检查远程 Docker 运行状态"""
        cmd = "docker info --format '{{.ServerVersion}}' 2>/dev/null || echo 'NOT_INSTALLED'"
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        version = stdout.read().decode().strip()

        if version == "NOT_INSTALLED":
            return {"installed": False, "version": ""}

        return {"installed": True, "version": version}

    def compose_up(self, compose_dir: str, env_file: str = None) -> str:
        """启动 Docker Compose 服务

        Args:
            compose_dir: docker-compose.yaml 所在目录
            env_file: .env 文件路径（可选）

        Returns:
            命令输出
        """
        cmd = f"cd {compose_dir} && docker compose up -d"
        if env_file:
            cmd = f"cd {compose_dir} && docker compose --env-file {env_file} up -d"

        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        return stdout.read().decode().strip() + stderr.read().decode().strip()

    def compose_down(self, compose_dir: str) -> str:
        """停止 Docker Compose 服务"""
        cmd = f"cd {compose_dir} && docker compose down"
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        return stdout.read().decode().strip()

    def compose_ps(self, compose_dir: str) -> list:
        """查看容器状态"""
        cmd = f"cd {compose_dir} && docker compose ps --format json 2>/dev/null || docker compose ps"
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        output = stdout.read().decode().strip()
        if not output:
            return []

        import json
        try:
            containers = []
            for line in output.split("\n"):
                if line.strip():
                    containers.append(json.loads(line))
            return containers
        except json.JSONDecodeError:
            return [{"raw": output}]

    def compose_logs(self, compose_dir: str, service: str = None,
                     tail: int = 100) -> str:
        """查看容器日志"""
        cmd = f"cd {compose_dir} && docker compose logs --tail {tail}"
        if service:
            cmd += f" {service}"
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        return stdout.read().decode().strip()

    def container_health(self, container_name: str) -> str:
        """检查容器健康状态"""
        cmd = f"docker inspect --format '{{{{.State.Health.Status}}}}' {container_name} 2>/dev/null || echo 'no_healthcheck'"
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        return stdout.read().decode().strip()