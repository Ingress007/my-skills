"""
Docker Commands - Docker command generator with type annotations
"""
from typing import Optional


class DockerCommands:
    """Docker command generator."""

    # ========== Container Commands ==========

    def ps(self, all: bool = False) -> str:
        """List containers."""
        cmd = "docker ps"
        if all:
            cmd += " -a"
        return cmd

    def logs(self, container: str, lines: int = 100, follow: bool = False) -> str:
        """Get container logs."""
        cmd = f"docker logs {container} --tail {lines}"
        if follow:
            cmd += " --follow"
        return cmd

    def start(self, container: str) -> str:
        """Start a container (requires confirmation)."""
        return f"docker start {container}"

    def stop(self, container: str, timeout: int = 10) -> str:
        """Stop a container (requires confirmation)."""
        return f"docker stop {container} --time {timeout}"

    def restart(self, container: str, timeout: int = 10) -> str:
        """Restart a container (requires confirmation)."""
        return f"docker restart {container} --time {timeout}"

    def rm(self, container: str, force: bool = False, volumes: bool = False) -> str:
        """Remove a container (requires confirmation)."""
        cmd = f"docker rm {container}"
        if force:
            cmd += " -f"
        if volumes:
            cmd += " -v"
        return cmd

    def exec_cmd(self, container: str, command: str, interactive: bool = False) -> str:
        """Execute command in container."""
        if interactive:
            return f"docker exec -it {container} {command}"
        return f"docker exec {container} {command}"

    def stats(self, container: Optional[str] = None, no_stream: bool = True) -> str:
        """Get container resource stats."""
        cmd = "docker stats"
        if no_stream:
            cmd += " --no-stream"
        if container:
            cmd += f" {container}"
        return cmd

    def inspect(self, target: str) -> str:
        """Inspect container or image."""
        return f"docker inspect {target}"

    def top(self, container: str) -> str:
        """Show container processes."""
        return f"docker top {container}"

    # ========== Image Commands ==========

    def images(self, all: bool = False) -> str:
        """List images."""
        cmd = "docker images"
        if all:
            cmd += " -a"
        return cmd

    def pull(self, image: str, registry: Optional[str] = None) -> str:
        """Pull image from registry."""
        if registry:
            return f"docker pull {registry}/{image}"
        return f"docker pull {image}"

    def push(self, image: str, registry: Optional[str] = None) -> str:
        """Push image to registry (requires confirmation)."""
        if registry:
            return f"docker push {registry}/{image}"
        return f"docker push {image}"

    def rmi(self, image: str, force: bool = False) -> str:
        """Remove image (requires confirmation)."""
        cmd = f"docker rmi {image}"
        if force:
            cmd += " -f"
        return cmd

    def tag(self, src_image: str, dest_image: str, registry: Optional[str] = None) -> str:
        """Tag an image."""
        if registry:
            return f"docker tag {src_image} {registry}/{dest_image}"
        return f"docker tag {src_image} {dest_image}"

    def build(self, tag: str, path: str, dockerfile: Optional[str] = None) -> str:
        """Build image (requires confirmation)."""
        cmd = f"docker build -t {tag} {path}"
        if dockerfile:
            cmd += f" -f {dockerfile}"
        return cmd

    def save(self, image: str, output_file: str) -> str:
        """Save image to tar file."""
        return f"docker save {image} -o {output_file}"

    def load(self, input_file: str) -> str:
        """Load image from tar file."""
        return f"docker load -i {input_file}"

    # ========== Registry Commands ==========

    def login(self, registry: Optional[str] = None) -> str:
        """Login to registry."""
        cmd = "docker login"
        if registry:
            cmd = f"docker login {registry}"
        return cmd

    def logout(self, registry: Optional[str] = None) -> str:
        """Logout from registry."""
        cmd = "docker logout"
        if registry:
            cmd = f"docker logout {registry}"
        return cmd

    # ========== Compose Commands ==========

    def compose_ps(self, file: Optional[str] = None) -> str:
        """List compose services."""
        cmd = "docker compose ps"
        if file:
            cmd = f"docker compose -f {file} ps"
        return cmd

    def compose_up(self, file: Optional[str] = None, detach: bool = True, build: bool = False) -> str:
        """Start compose services (requires confirmation)."""
        cmd = "docker compose"
        if file:
            cmd += f" -f {file}"
        cmd += " up"
        if detach:
            cmd += " -d"
        if build:
            cmd += " --build"
        return cmd

    def compose_down(self, file: Optional[str] = None, volumes: bool = False, remove_orphans: bool = False) -> str:
        """Stop compose services (requires confirmation)."""
        cmd = "docker compose"
        if file:
            cmd += f" -f {file}"
        cmd += " down"
        if volumes:
            cmd += " -v"
        if remove_orphans:
            cmd += " --remove-orphans"
        return cmd

    def compose_logs(self, file: Optional[str] = None, service: Optional[str] = None, lines: int = 100, follow: bool = False) -> str:
        """Get compose logs."""
        cmd = "docker compose"
        if file:
            cmd += f" -f {file}"
        cmd += f" logs --tail {lines}"
        if service:
            cmd += f" {service}"
        if follow:
            cmd += " --follow"
        return cmd

    def compose_pull(self, file: Optional[str] = None) -> str:
        """Pull compose images."""
        cmd = "docker compose pull"
        if file:
            cmd = f"docker compose -f {file} pull"
        return cmd

    def compose_restart(self, file: Optional[str] = None, service: Optional[str] = None) -> str:
        """Restart compose services (requires confirmation)."""
        cmd = "docker compose"
        if file:
            cmd += f" -f {file}"
        cmd += " restart"
        if service:
            cmd += f" {service}"
        return cmd

    def compose_stop(self, file: Optional[str] = None, service: Optional[str] = None) -> str:
        """Stop compose services."""
        cmd = "docker compose"
        if file:
            cmd += f" -f {file}"
        cmd += " stop"
        if service:
            cmd += f" {service}"
        return cmd

    def compose_start(self, file: Optional[str] = None, service: Optional[str] = None) -> str:
        """Start compose services."""
        cmd = "docker compose"
        if file:
            cmd += f" -f {file}"
        cmd += " start"
        if service:
            cmd += f" {service}"
        return cmd

    def compose_build(self, file: Optional[str] = None, service: Optional[str] = None) -> str:
        """Build compose images (requires confirmation)."""
        cmd = "docker compose"
        if file:
            cmd += f" -f {file}"
        cmd += " build"
        if service:
            cmd += f" {service}"
        return cmd

    # ========== Network Commands ==========

    def network_ls(self) -> str:
        """List networks."""
        return "docker network ls"

    def network_create(self, name: str, driver: Optional[str] = None) -> str:
        """Create network."""
        cmd = f"docker network create {name}"
        if driver:
            cmd += f" --driver {driver}"
        return cmd

    def network_rm(self, name: str) -> str:
        """Remove network."""
        return f"docker network rm {name}"

    def network_inspect(self, name: str) -> str:
        """Inspect network."""
        return f"docker network inspect {name}"

    # ========== Volume Commands ==========

    def volume_ls(self) -> str:
        """List volumes."""
        return "docker volume ls"

    def volume_create(self, name: str) -> str:
        """Create volume."""
        return f"docker volume create {name}"

    def volume_rm(self, name: str) -> str:
        """Remove volume."""
        return f"docker volume rm {name}"

    def volume_inspect(self, name: str) -> str:
        """Inspect volume."""
        return f"docker volume inspect {name}"

    # ========== System Commands ==========

    def info(self) -> str:
        """Docker system info."""
        return "docker info"

    def version(self) -> str:
        """Docker version."""
        return "docker version"

    def df(self) -> str:
        """Docker disk usage."""
        return "docker system df"

    def events(self, since: Optional[str] = None, until: Optional[str] = None) -> str:
        """Docker events."""
        cmd = "docker events"
        if since:
            cmd += f" --since {since}"
        if until:
            cmd += f" --until {until}"
        return cmd