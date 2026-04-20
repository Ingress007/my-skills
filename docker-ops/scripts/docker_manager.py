"""
Docker Manager - Docker and Docker Compose management CLI
Uses SSH config from linux-ops for server connections.
"""
import sys
import os
import json
import argparse
from typing import Dict, Any, Optional

# Import from shared module
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_shared_path = os.path.join(_project_root, "shared")
sys.path.insert(0, _shared_path)

from ssh_client import SSHClient, create_ssh_client
from ssh_config_parser import get_host_config, list_hosts
from type_defs import SSHServerConfig

# Import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config_manager import ConfigManager
from docker_commands import DockerCommands


class DockerManager:
    """Docker management via SSH."""

    def __init__(self, timeout: Optional[int] = None):
        """
        Initialize Docker Manager.

        Args:
            timeout: SSH connection timeout in seconds
        """
        self.cm: ConfigManager = ConfigManager()
        self.dc: DockerCommands = DockerCommands()
        self.client: SSHClient = create_ssh_client(timeout)

    def execute(
        self,
        alias: str,
        command: str,
        confirm: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a Docker command on a server.

        Args:
            alias: Host alias from SSH config
            command: Docker command to execute
            confirm: Whether to confirm sensitive commands

        Returns:
            dict: {status, stdout, stderr, exit_code}
        """
        # Check command safety
        allowed, requires_conf, reason = self.cm.check_command(command)
        if not allowed:
            return {
                "status": "error",
                "message": f"Command blocked: {reason}",
                "exit_code": -1
            }

        if requires_conf and not confirm:
            return {
                "status": "error",
                "message": f"Command requires confirmation: {reason}. Rerun with --confirm flag.",
                "exit_code": -1
            }

        server = self.cm.get_server(alias)
        if not server:
            return {
                "status": "error",
                "message": f"Host '{alias}' not found in SSH config.",
                "exit_code": -1
            }

        # Execute via shared SSH client
        result = self.client.execute(server, command)

        if result["status"] == "error":
            return {
                "status": "error",
                "message": result.get("message", "Unknown error"),
                "exit_code": result["exit_code"]
            }
        return {
            "status": "success",
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "exit_code": result["exit_code"]
        }

    def execute_script(
        self,
        alias: str,
        script_path: str
    ) -> Dict[str, Any]:
        """
        Execute a local script on a remote server.

        Args:
            alias: Host alias from SSH config
            script_path: Path to local script file

        Returns:
            dict: {status, stdout, stderr, exit_code}
        """
        server = self.cm.get_server(alias)
        if not server:
            return {
                "status": "error",
                "message": f"Host '{alias}' not found in SSH config.",
                "exit_code": -1
            }

        result = self.client.execute_script_file(server, script_path)

        if result["status"] == "error":
            return {
                "status": "error",
                "message": result.get("message", "Unknown error"),
                "exit_code": result["exit_code"]
            }
        return {
            "status": "success",
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "exit_code": result["exit_code"]
        }

    def diagnose(self, alias: str) -> Dict[str, Any]:
        """Run Docker diagnostic script on server."""
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diagnose.sh")
        return self.execute_script(alias, script_path)


def main() -> None:
    # Force UTF-8 on Windows
    if sys.platform == 'win32':
        sys.stdin.reconfigure(encoding='utf-8')
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(
        description="Docker Manager - Docker and Docker Compose management via SSH"
    )
    parser.add_argument("alias", help="Host alias from SSH config")
    subparsers = parser.add_subparsers(dest="action", help="Docker action")

    # ========== Container Commands ==========

    # ps
    ps_parser = subparsers.add_parser("ps", help="List containers")
    ps_parser.add_argument("--all", "-a", action="store_true", help="Show all containers")

    # logs
    logs_parser = subparsers.add_parser("logs", help="View container logs")
    logs_parser.add_argument("container", help="Container name or ID")
    logs_parser.add_argument("--lines", "-n", type=int, default=100, help="Number of lines")

    # start
    start_parser = subparsers.add_parser("start", help="Start container")
    start_parser.add_argument("container", help="Container name or ID")
    start_parser.add_argument("--confirm", action="store_true", help="Confirm execution")

    # stop
    stop_parser = subparsers.add_parser("stop", help="Stop container")
    stop_parser.add_argument("container", help="Container name or ID")
    stop_parser.add_argument("--timeout", "-t", type=int, default=10, help="Timeout in seconds")
    stop_parser.add_argument("--confirm", action="store_true", help="Confirm execution")

    # restart
    restart_parser = subparsers.add_parser("restart", help="Restart container")
    restart_parser.add_argument("container", help="Container name or ID")
    restart_parser.add_argument("--timeout", "-t", type=int, default=10, help="Timeout in seconds")
    restart_parser.add_argument("--confirm", action="store_true", help="Confirm execution")

    # rm
    rm_parser = subparsers.add_parser("rm", help="Remove container")
    rm_parser.add_argument("container", help="Container name or ID")
    rm_parser.add_argument("--force", "-f", action="store_true", help="Force removal")
    rm_parser.add_argument("--volumes", "-v", action="store_true", help="Remove volumes")
    rm_parser.add_argument("--confirm", action="store_true", help="Confirm execution")

    # exec
    exec_parser = subparsers.add_parser("exec", help="Execute command in container")
    exec_parser.add_argument("container", help="Container name or ID")
    exec_parser.add_argument("command", help="Command to execute")

    # stats
    stats_parser = subparsers.add_parser("stats", help="Container resource stats")
    stats_parser.add_argument("container", nargs="?", default=None, help="Container name or ID (optional)")

    # inspect
    inspect_parser = subparsers.add_parser("inspect", help="Inspect container or image")
    inspect_parser.add_argument("target", help="Container or image name/ID")

    # ========== Image Commands ==========

    # images
    images_parser = subparsers.add_parser("images", help="List images")
    images_parser.add_argument("--all", "-a", action="store_true", help="Show all images")

    # pull
    pull_parser = subparsers.add_parser("pull", help="Pull image")
    pull_parser.add_argument("image", help="Image name")
    pull_parser.add_argument("--registry", help="Registry URL (optional)")

    # push
    push_parser = subparsers.add_parser("push", help="Push image")
    push_parser.add_argument("image", help="Image name")
    push_parser.add_argument("--registry", help="Registry URL (optional)")
    push_parser.add_argument("--confirm", action="store_true", help="Confirm execution")

    # rmi
    rmi_parser = subparsers.add_parser("rmi", help="Remove image")
    rmi_parser.add_argument("image", help="Image name or ID")
    rmi_parser.add_argument("--force", "-f", action="store_true", help="Force removal")
    rmi_parser.add_argument("--confirm", action="store_true", help="Confirm execution")

    # login
    login_parser = subparsers.add_parser("login", help="Login to registry")
    login_parser.add_argument("registry", nargs="?", default=None, help="Registry URL (optional)")

    # logout
    logout_parser = subparsers.add_parser("logout", help="Logout from registry")
    logout_parser.add_argument("registry", nargs="?", default=None, help="Registry URL (optional)")

    # ========== Compose Commands ==========

    # compose ps
    compose_ps = subparsers.add_parser("compose-ps", help="List compose services")
    compose_ps.add_argument("--file", "-f", help="Compose file path")

    # compose up
    compose_up = subparsers.add_parser("compose-up", help="Start compose services")
    compose_up.add_argument("--file", "-f", help="Compose file path")
    compose_up.add_argument("--build", action="store_true", help="Build before starting")
    compose_up.add_argument("--confirm", action="store_true", help="Confirm execution")

    # compose down
    compose_down = subparsers.add_parser("compose-down", help="Stop compose services")
    compose_down.add_argument("--file", "-f", help="Compose file path")
    compose_down.add_argument("--volumes", "-v", action="store_true", help="Remove volumes")
    compose_down.add_argument("--remove-orphans", action="store_true", help="Remove orphan containers")
    compose_down.add_argument("--confirm", action="store_true", help="Confirm execution")

    # compose logs
    compose_logs = subparsers.add_parser("compose-logs", help="View compose logs")
    compose_logs.add_argument("--file", "-f", help="Compose file path")
    compose_logs.add_argument("service", nargs="?", default=None, help="Service name (optional)")
    compose_logs.add_argument("--lines", "-n", type=int, default=100, help="Number of lines")

    # compose pull
    compose_pull = subparsers.add_parser("compose-pull", help="Pull compose images")
    compose_pull.add_argument("--file", "-f", help="Compose file path")

    # compose restart
    compose_restart = subparsers.add_parser("compose-restart", help="Restart compose services")
    compose_restart.add_argument("--file", "-f", help="Compose file path")
    compose_restart.add_argument("service", nargs="?", default=None, help="Service name (optional)")
    compose_restart.add_argument("--confirm", action="store_true", help="Confirm execution")

    # compose stop
    compose_stop = subparsers.add_parser("compose-stop", help="Stop compose services")
    compose_stop.add_argument("--file", "-f", help="Compose file path")
    compose_stop.add_argument("service", nargs="?", default=None, help="Service name (optional)")

    # compose start
    compose_start = subparsers.add_parser("compose-start", help="Start compose services")
    compose_start.add_argument("--file", "-f", help="Compose file path")
    compose_start.add_argument("service", nargs="?", default=None, help="Service name (optional)")

    # compose build
    compose_build = subparsers.add_parser("compose-build", help="Build compose images")
    compose_build.add_argument("--file", "-f", help="Compose file path")
    compose_build.add_argument("service", nargs="?", default=None, help="Service name (optional)")
    compose_build.add_argument("--confirm", action="store_true", help="Confirm execution")

    # ========== Diagnostic ==========

    diagnose_parser = subparsers.add_parser("diagnose", help="Run Docker diagnostic")

    # Parse arguments
    args = parser.parse_args()

    if not args.action:
        parser.print_help()
        sys.exit(1)

    manager = DockerManager()

    # Handle commands
    cmd: Optional[str] = None
    confirm = getattr(args, 'confirm', False)

    # Container commands
    if args.action == "ps":
        cmd = manager.dc.ps(all=args.all)
    elif args.action == "logs":
        cmd = manager.dc.logs(args.container, lines=args.lines)
    elif args.action == "start":
        cmd = manager.dc.start(args.container)
    elif args.action == "stop":
        cmd = manager.dc.stop(args.container, timeout=args.timeout)
    elif args.action == "restart":
        cmd = manager.dc.restart(args.container, timeout=args.timeout)
    elif args.action == "rm":
        cmd = manager.dc.rm(args.container, force=args.force, volumes=args.volumes)
    elif args.action == "exec":
        cmd = manager.dc.exec_cmd(args.container, args.command)
    elif args.action == "stats":
        cmd = manager.dc.stats(args.container)
    elif args.action == "inspect":
        cmd = manager.dc.inspect(args.target)

    # Image commands
    elif args.action == "images":
        cmd = manager.dc.images(all=args.all)
    elif args.action == "pull":
        cmd = manager.dc.pull(args.image, registry=args.registry)
    elif args.action == "push":
        cmd = manager.dc.push(args.image, registry=args.registry)
    elif args.action == "rmi":
        cmd = manager.dc.rmi(args.image, force=args.force)
    elif args.action == "login":
        cmd = manager.dc.login(args.registry)
    elif args.action == "logout":
        cmd = manager.dc.logout(args.registry)

    # Compose commands
    elif args.action == "compose-ps":
        cmd = manager.dc.compose_ps(file=args.file)
    elif args.action == "compose-up":
        cmd = manager.dc.compose_up(file=args.file, build=args.build)
    elif args.action == "compose-down":
        cmd = manager.dc.compose_down(file=args.file, volumes=args.volumes, remove_orphans=args.remove_orphans)
    elif args.action == "compose-logs":
        cmd = manager.dc.compose_logs(file=args.file, service=args.service, lines=args.lines)
    elif args.action == "compose-pull":
        cmd = manager.dc.compose_pull(file=args.file)
    elif args.action == "compose-restart":
        cmd = manager.dc.compose_restart(file=args.file, service=args.service)
    elif args.action == "compose-stop":
        cmd = manager.dc.compose_stop(file=args.file, service=args.service)
    elif args.action == "compose-start":
        cmd = manager.dc.compose_start(file=args.file, service=args.service)
    elif args.action == "compose-build":
        cmd = manager.dc.compose_build(file=args.file, service=args.service)

    # Diagnostic
    elif args.action == "diagnose":
        result = manager.diagnose(args.alias)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if result["status"] == "error":
            sys.exit(1)
        return

    if cmd:
        result = manager.execute(args.alias, cmd, confirm)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if result["status"] == "error":
            sys.exit(1)


if __name__ == "__main__":
    main()