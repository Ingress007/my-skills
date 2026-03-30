"""
SSH Manager - Execute commands on servers via SSH using .ssh/config
"""
import paramiko
import sys
import os
import json
import argparse

# Add current dir to path to import config_manager
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config_manager import ConfigManager


class SSHManager:
    def __init__(self):
        self.cm = ConfigManager()

    def execute(self, alias, command, confirm=False):
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

        server = self.cm.get_server(alias)
        if not server:
            return {
                "status": "error",
                "message": f"Host '{alias}' not found in SSH config.",
                "exit_code": -1
            }

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            connect_kwargs = {
                "hostname": server["hostname"],
                "port": int(server["port"]),
                "username": server["user"] or "root",
                "timeout": 10
            }

            if server.get("identityfile"):
                connect_kwargs["key_filename"] = server["identityfile"]

            client.connect(**connect_kwargs)

            stdin, stdout, stderr = client.exec_command(command)
            exit_code = stdout.channel.recv_exit_status()
            out = stdout.read().decode('utf-8', errors='replace')
            err = stderr.read().decode('utf-8', errors='replace')

            return {
                "status": "success",
                "stdout": out,
                "stderr": err,
                "exit_code": exit_code
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "exit_code": -1
            }
        finally:
            client.close()

    def execute_script(self, alias, script_path):
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

        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to read script: {str(e)}",
                "exit_code": -1
            }

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            connect_kwargs = {
                "hostname": server["hostname"],
                "port": int(server["port"]),
                "username": server["user"] or "root",
                "timeout": 10
            }
            if server.get("identityfile"):
                connect_kwargs["key_filename"] = server["identityfile"]

            client.connect(**connect_kwargs)

            # Execute bash -s and write script to stdin
            stdin, stdout, stderr = client.exec_command("bash -s")
            stdin.write(script_content)
            stdin.flush()
            stdin.channel.shutdown_write()  # Signal EOF

            exit_code = stdout.channel.recv_exit_status()
            out = stdout.read().decode('utf-8', errors='replace')
            err = stderr.read().decode('utf-8', errors='replace')

            return {
                "status": "success",
                "stdout": out,
                "stderr": err,
                "exit_code": exit_code
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "exit_code": -1
            }
        finally:
            client.close()


def main():
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