"""
SSH Manager - Execute commands on servers via SSH using .ssh/config
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

# Import local config manager
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config_manager import ConfigManager


class SSHManager:
    """SSH command execution manager"""

    def __init__(self, timeout: Optional[int] = None):
        """
        Initialize SSH Manager.

        Args:
            timeout: SSH connection timeout in seconds
        """
        self.cm: ConfigManager = ConfigManager()
        self.client: SSHClient = create_ssh_client(timeout)

    def execute(
        self,
        alias: str,
        command: str,
        confirm: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a command on a server identified by SSH config alias.

        Args:
            alias: Host alias from SSH config
            command: Command to execute
            confirm: Whether to confirm sensitive commands

        Returns:
            dict: {status, stdout, stderr, exit_code} or {status, message, exit_code} on error
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

        # Get server config
        server = self.cm.get_server(alias)
        if not server:
            return {
                "status": "error",
                "message": f"Host '{alias}' not found in SSH config.",
                "exit_code": -1
            }

        # Execute via shared SSH client
        result = self.client.execute(server, command)

        # Convert to compatible format
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


def main() -> None:
    # Force UTF-8 for stdin/stdout/stderr on Windows
    if sys.platform == 'win32':
        sys.stdin.reconfigure(encoding='utf-8')
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(
        description="SSH Manager for AI Agent - Uses .ssh/config for server connections"
    )
    subparsers = parser.add_subparsers(dest="action", help="Action to perform")

    # execute
    exec_parser = subparsers.add_parser("exec", help="Execute command on server")
    exec_parser.add_argument("alias", help="Host alias from SSH config")
    exec_parser.add_argument("command", help="Command to execute")
    exec_parser.add_argument("--confirm", action="store_true",
                             help="Confirm execution of sensitive commands")

    # diagnose
    diag_parser = subparsers.add_parser("diagnose", help="Run system diagnostic script on server")
    diag_parser.add_argument("alias", help="Host alias from SSH config")

    # list-servers
    subparsers.add_parser("list-servers", help="List all hosts from SSH config")

    args = parser.parse_args()

    manager = SSHManager()

    if args.action == "exec":
        result = manager.execute(args.alias, args.command, args.confirm)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if result["status"] == "error":
            sys.exit(1)

    elif args.action == "diagnose":
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diagnose.sh")
        result = manager.execute_script(args.alias, script_path)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if result["status"] == "error":
            sys.exit(1)

    elif args.action == "list-servers":
        servers = manager.cm.list_servers()
        print(json.dumps({"hosts": servers}, indent=2, ensure_ascii=False))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()