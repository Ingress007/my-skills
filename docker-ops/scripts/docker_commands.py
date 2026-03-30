"""
Docker Commands - Docker container, image, and compose command generator
"""


class DockerCommands:
    """Docker command generator."""

    # ========== Container Commands ==========

    def ps(self, all=False):
        """List containers."""
        cmd = "docker ps"
        if all:
            cmd += " -a"
        return cmd

    def logs(self, container, lines=100, follow=False):
        """Get container logs."""
        cmd = f"docker logs {container} --tail {lines}"
        if follow:
            cmd += " --follow"
        return cmd

    def start(self, container):
        """Start a container (requires confirmation)."""
        return f"docker start {container}"

    def stop(self, container, timeout=10):
        """Stop a container (requires confirmation)."""
        return f"docker stop {container} --time {timeout}"

    def restart(self, container, timeout=10):
        """Restart a container (requires confirmation)."""
        return f"docker restart {container} --time {timeout}"

    def rm(self, container, force=False, volumes=False):
        """Remove a container (requires confirmation)."""
        cmd = f"docker rm {container}"
        if force:
            cmd += " -f"
        if volumes:
            cmd += " -v"
        return cmd

    def exec_cmd(self, container, command, interactive=False):
        """Execute command in container."""
        if interactive:
            return f"docker exec -it {container} {command}"
        return f"docker exec {container} {command}"

    def stats(self, container=None, no_stream=True):
        """Get container resource stats."""
        cmd = "docker stats"
        if no_stream:
            cmd += " --no-stream"
        if container:
            cmd += f" {container}"
        return cmd

    def inspect(self, target):
        """Inspect container or image."""
        return f"docker inspect {target}"

    def top(self, container):
        """Show container processes."""
        return f"docker top {container}"

    # ========== Image Commands ==========

    def images(self, all=False):
        """List images."""
        cmd = "docker images"
        if all:
            cmd += " -a"
        return cmd

    def pull(self, image, registry=None):
        """Pull image from registry."""
        if registry:
            return f"docker pull {registry}/{image}"
        return f"docker pull {image}"

    def push(self, image, registry=None):
        """Push image to registry (requires confirmation)."""
        if registry:
            return f"docker push {registry}/{image}"
        return f"docker push {image}"

    def rmi(self, image, force=False):
        """Remove image (requires confirmation)."""
        cmd = f"docker rmi {image}"
        if force:
            cmd += " -f"
        return cmd

    def tag(self, src_image, dest_image, registry=None):
        """Tag an image."""
        if registry:
            return f"docker tag {src_image} {registry}/{dest_image}"
        return f"docker tag {src_image} {dest_image}"

    def build(self, tag, path, dockerfile=None):
        """Build image (requires confirmation)."""
        cmd = f"docker build -t {tag} {path}"
        if dockerfile:
            cmd += f" -f {dockerfile}"
        return cmd

    def save(self, image, output_file):
        """Save image to tar file."""
        return f"docker save {image} -o {output_file}"

    def load(self, input_file):
        """Load image from tar file."""
        return f"docker load -i {input_file}"

    # ========== Registry Commands ==========

    def login(self, registry=None):
        """Login to registry."""
        cmd = "docker login"
        if registry:
            cmd = f"docker login {registry}"
        return cmd

    def logout(self, registry=None):
        """Logout from registry."""
        cmd = "docker logout"
        if registry:
            cmd = f"docker logout {registry}"
        return cmd

    # ========== Compose Commands ==========

    def compose_ps(self, file=None):
        """List compose services."""
        cmd = "docker compose ps"
        if file:
            cmd = f"docker compose -f {file} ps"
        return cmd

    def compose_up(self, file=None, detach=True, build=False):
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

    def compose_down(self, file=None, volumes=False, remove_orphans=False):
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

    def compose_logs(self, file=None, service=None, lines=100, follow=False):
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

    def compose_pull(self, file=None):
        """Pull compose images."""
        cmd = "docker compose pull"
        if file:
            cmd = f"docker compose -f {file} pull"
        return cmd

    def compose_restart(self, file=None, service=None):
        """Restart compose services (requires confirmation)."""
        cmd = "docker compose"
        if file:
            cmd += f" -f {file}"
        cmd += " restart"
        if service:
            cmd += f" {service}"
        return cmd

    def compose_stop(self, file=None, service=None):
        """Stop compose services."""
        cmd = "docker compose"
        if file:
            cmd += f" -f {file}"
        cmd += " stop"
        if service:
            cmd += f" {service}"
        return cmd

    def compose_start(self, file=None, service=None):
        """Start compose services."""
        cmd = "docker compose"
        if file:
            cmd += f" -f {file}"
        cmd += " start"
        if service:
            cmd += f" {service}"
        return cmd

    def compose_build(self, file=None, service=None):
        """Build compose images (requires confirmation)."""
        cmd = "docker compose"
        if file:
            cmd += f" -f {file}"
        cmd += " build"
        if service:
            cmd += f" {service}"
        return cmd

    # ========== Network Commands ==========

    def network_ls(self):
        """List networks."""
        return "docker network ls"

    def network_create(self, name, driver=None):
        """Create network."""
        cmd = f"docker network create {name}"
        if driver:
            cmd += f" --driver {driver}"
        return cmd

    def network_rm(self, name):
        """Remove network."""
        return f"docker network rm {name}"

    def network_inspect(self, name):
        """Inspect network."""
        return f"docker network inspect {name}"

    # ========== Volume Commands ==========

    def volume_ls(self):
        """List volumes."""
        return "docker volume ls"

    def volume_create(self, name):
        """Create volume."""
        return f"docker volume create {name}"

    def volume_rm(self, name):
        """Remove volume."""
        return f"docker volume rm {name}"

    def volume_inspect(self, name):
        """Inspect volume."""
        return f"docker volume inspect {name}"

    # ========== System Commands ==========

    def info(self):
        """Docker system info."""
        return "docker info"

    def version(self):
        """Docker version."""
        return "docker version"

    def df(self):
        """Docker disk usage."""
        return "docker system df"

    def events(self, since=None, until=None):
        """Docker events."""
        cmd = "docker events"
        if since:
            cmd += f" --since {since}"
        if until:
            cmd += f" --until {until}"
        return cmd