import paramiko
import sys
import os
import json
import argparse
import socket

# Add current dir to path to import config_manager
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config_manager import ConfigManager

class SSHManager:
    def __init__(self):
        self.cm = ConfigManager()

    def execute(self, alias, command, confirm=False):
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
                "message": f"Server '{alias}' not found.",
                "exit_code": -1
            }

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            connect_kwargs = {
                "hostname": server["hostname"],
                "port": int(server["port"]),
                "username": server["username"],
                "timeout": 10
            }
            
            if server.get("key_path"):
                connect_kwargs["key_filename"] = server["key_path"]
            elif server.get("password"):
                connect_kwargs["password"] = server["password"]
            
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
            
        except socket.timeout:
             return {
                "status": "error",
                "message": "Connection timed out",
                "exit_code": -1
            }
        except paramiko.AuthenticationException:
             return {
                "status": "error",
                "message": "Authentication failed",
                "exit_code": -1
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
        server = self.cm.get_server(alias)
        if not server:
            return {
                "status": "error",
                "message": f"Server '{alias}' not found.",
                "exit_code": -1
            }
        
        try:
            with open(script_path, 'r') as f:
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
                "username": server["username"],
                "timeout": 10
            }
            if server.get("key_path"):
                connect_kwargs["key_filename"] = server["key_path"]
            elif server.get("password"):
                connect_kwargs["password"] = server["password"]
            
            client.connect(**connect_kwargs)
            
            # Execute bash -s and write script to stdin
            stdin, stdout, stderr = client.exec_command("bash -s")
            stdin.write(script_content)
            stdin.flush()
            stdin.channel.shutdown_write() # Signal EOF
            
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
    # Force UTF-8 for stdin/stdout/stderr
    if sys.platform == 'win32':
        sys.stdin.reconfigure(encoding='utf-8')
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description="SSH Manager for AI Agent")
    subparsers = parser.add_subparsers(dest="action", help="Action to perform")

    # execute
    exec_parser = subparsers.add_parser("exec", help="Execute command on server")
    exec_parser.add_argument("alias", help="Server alias")
    exec_parser.add_argument("command", help="Command to execute")
    exec_parser.add_argument("--confirm", action="store_true", help="Confirm execution of sensitive commands")

    # add-server
    add_parser = subparsers.add_parser("add-server", help="Add a new server")
    add_parser.add_argument("alias", help="Server alias")
    add_parser.add_argument("hostname", help="Server hostname or IP")
    add_parser.add_argument("--port", default=22, type=int, help="SSH port")
    add_parser.add_argument("--user", required=True, help="SSH username")
    add_parser.add_argument("--password", help="SSH password (will prompt if not provided)")
    add_parser.add_argument("--key", help="Path to SSH private key")

    # remove-server
    rm_parser = subparsers.add_parser("remove-server", help="Remove a server")
    rm_parser.add_argument("alias", help="Server alias")

    # list-servers
    subparsers.add_parser("list-servers", help="List all configured servers")

    # diagnose
    diag_parser = subparsers.add_parser("diagnose", help="Run diagnostic script on server")
    diag_parser.add_argument("alias", help="Server alias")

    args = parser.parse_args()
    
    manager = SSHManager()

    if args.action == "exec":
        result = manager.execute(args.alias, args.command, args.confirm)
        print(json.dumps(result, indent=2))
        if result["status"] == "error":
            sys.exit(1)

    elif args.action == "diagnose":
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diagnose.sh")
        result = manager.execute_script(args.alias, script_path)
        print(json.dumps(result, indent=2))
        if result["status"] == "error":
            sys.exit(1)
            
    elif args.action == "add-server":
        # 交互式输入密码，避免命令行历史泄露
        password = args.password
        if not password and not args.key:
            import getpass
            password = getpass.getpass("Password: ")

        manager.cm.add_server(args.alias, args.hostname, args.port, args.user, password, args.key)
        print(json.dumps({"status": "success", "message": f"Server {args.alias} added."}))
        
    elif args.action == "remove-server":
        if manager.cm.remove_server(args.alias):
            print(json.dumps({"status": "success", "message": f"Server {args.alias} removed."}))
        else:
            print(json.dumps({"status": "error", "message": f"Server {args.alias} not found."}))
            
    elif args.action == "list-servers":
        servers = manager.cm.list_servers()
        print(json.dumps({"servers": servers}, indent=2))
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
