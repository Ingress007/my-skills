"""
Server Manager - Add and remove SSH server configurations
"""
import sys
import os
import json
import argparse
import getpass
from typing import Dict, Any, Optional

# Import from shared module
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_shared_path = os.path.join(_project_root, "shared")
sys.path.insert(0, _shared_path)

from ssh_client import SSHClient, create_ssh_client, add_to_known_hosts, get_known_hosts_path
from ssh_config_parser import (
    get_ssh_config_path,
    get_ssh_dir,
    list_hosts,
    host_exists,
    generate_unique_name,
    add_host,
    remove_host,
    get_host_config
)
from ssh_key_manager import ensure_key_exists, get_default_key_path
from type_defs import ServerAddConfig, SSHServerConfig


class ServerManager:
    """SSH server configuration manager"""

    def __init__(self, config_path: Optional[str] = None, timeout: int = 10):
        """
        Initialize Server Manager.

        Args:
            config_path: Custom SSH config path (optional)
            timeout: SSH connection timeout in seconds
        """
        self.config_path = config_path or get_ssh_config_path()
        self.client = create_ssh_client(timeout)

    def add_server(
        self,
        name: str,
        ip: str,
        password: str,
        port: int = 22,
        user: str = "root",
        key_path: Optional[str] = None,
        verified_host_key: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Add a new server with password authentication, then setup key-based auth.

        Args:
            name: Server alias name
            ip: Server IP address
            port: SSH port (default 22)
            user: SSH username (default root)
            password: Password for initial connection
            key_path: Custom SSH key path (optional)
            verified_host_key: Pre-verified host key object (optional)

        Returns:
            dict: Result with status and message
        """
        result = {
            "status": "error",
            "message": "",
            "host_name": None,
            "steps": []
        }

        # Step 1: Generate unique name if duplicate
        original_name = name
        name = generate_unique_name(name, self.config_path)
        if name != original_name:
            result["steps"].append({
                "step": "name_check",
                "status": "warning",
                "message": f"名称 '{original_name}' 已存在，使用 '{name}'"
            })
        else:
            result["steps"].append({
                "step": "name_check",
                "status": "success",
                "message": f"名称 '{name}' 可用"
            })

        result["host_name"] = name

        # Step 2: Test password connection with verified host key
        server_config: ServerAddConfig = {
            "name": name,
            "ip": ip,
            "port": port,
            "user": user,
            "password": password
        }
        conn_result = self.client.connect_with_password(server_config, verified_host_key)
        if conn_result["status"] != "success":
            result["message"] = f"密码连接失败: {conn_result['message']}"
            result["steps"].append({
                "step": "password_connect",
                "status": "error",
                "message": conn_result["message"]
            })
            return result

        result["steps"].append({
            "step": "password_connect",
            "status": "success",
            "message": "密码连接成功"
        })

        # Step 3: Ensure SSH key exists
        if key_path is None:
            key_path = get_default_key_path()

        key_success, key_message, public_key = ensure_key_exists(key_path)
        if not key_success or not public_key:
            result["message"] = f"SSH Key 问题: {key_message}"
            result["steps"].append({
                "step": "ssh_key",
                "status": "error",
                "message": key_message
            })
            return result

        result["steps"].append({
            "step": "ssh_key",
            "status": "success",
            "message": key_message
        })

        # Step 4: Upload public key to server
        upload_result = self.client.upload_ssh_key(server_config, public_key, verified_host_key)
        if upload_result["status"] != "success":
            result["message"] = f"上传公钥失败: {upload_result['message']}"
            result["steps"].append({
                "step": "upload_key",
                "status": "error",
                "message": upload_result["message"]
            })
            return result

        result["steps"].append({
            "step": "upload_key",
            "status": "success",
            "message": "公钥上传成功"
        })

        # Step 5: Add to SSH config
        add_success = add_host(
            host=name,
            hostname=ip,
            user=user,
            port=port,
            identityfile=key_path,
            config_path=self.config_path
        )
        if not add_success:
            result["message"] = (
                "写入 SSH 配置失败。"
                "注意：公钥已上传至远程服务器 ~/.ssh/authorized_keys，"
                "请手动补充本地 SSH 配置，或通过密码登录远程服务器清理 ~/.ssh/authorized_keys 文件。"
                f"待清理的服务器: {user}@{ip}:{port}"
            )
            result["steps"].append({
                "step": "write_config",
                "status": "error",
                "message": "写入 SSH 配置失败"
            })
            return result

        result["steps"].append({
            "step": "write_config",
            "status": "success",
            "message": f"SSH 配置已写入: {self.config_path}"
        })

        # Step 6: Verify key-based authentication
        test_config: SSHServerConfig = {
            "hostname": ip,
            "user": user,
            "port": port,
            "identityfile": key_path
        }
        test_result = self.client.test_key_auth(test_config)
        if test_result["status"] != "success":
            result["message"] = f"Key 认证验证失败: {test_result['message']}"
            result["steps"].append({
                "step": "verify_key_auth",
                "status": "error",
                "message": test_result["message"]
            })
            return result

        result["steps"].append({
            "step": "verify_key_auth",
            "status": "success",
            "message": "Key 认证验证成功"
        })

        result["status"] = "success"
        result["message"] = f"服务器 '{name}' 添加成功，后续连接将使用 SSH Key 认证"
        return result

    def remove_server(self, name: str) -> Dict[str, Any]:
        """
        Remove a server from SSH config.

        Args:
            name: Server alias name to remove

        Returns:
            dict: Result with status and message
        """
        result = {
            "status": "error",
            "message": ""
        }

        # Check if host exists
        if not host_exists(name, self.config_path):
            result["message"] = f"服务器 '{name}' 不存在"
            return result

        # Get host config before removal
        host_config = get_host_config(name, self.config_path)
        
        # Remove from config
        if remove_host(name, self.config_path):
            result["status"] = "success"
            result["message"] = f"服务器 '{name}' 已从 SSH 配置中删除"
            result["removed_config"] = host_config
        else:
            result["message"] = f"删除服务器 '{name}' 失败"

        return result

    def list_servers(self) -> Dict[str, Any]:
        """
        List all servers in SSH config.

        Returns:
            dict: Result with server list
        """
        hosts = list_hosts(self.config_path)
        return {
            "status": "success",
            "config_path": self.config_path,
            "hosts": hosts,
            "count": len(hosts)
        }


def main() -> None:
    # Force UTF-8 for stdin/stdout/stderr on Windows
    if sys.platform == 'win32':
        sys.stdin.reconfigure(encoding='utf-8')
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(
        description="Server Manager - Add and remove SSH server configurations"
    )
    parser.add_argument(
        "--config-path",
        help="Custom SSH config path (default: ~/.ssh/config)"
    )
    
    subparsers = parser.add_subparsers(dest="action", help="Action to perform")

    # add
    add_parser = subparsers.add_parser("add", help="Add a new server")
    add_parser.add_argument("name", help="Server alias name")
    add_parser.add_argument("ip", help="Server IP address")
    add_parser.add_argument("--port", type=int, default=22, help="SSH port (default: 22)")
    add_parser.add_argument("--user", default="root", help="SSH username (default: root)")
    add_parser.add_argument("--key-path", help="Custom SSH key path")
    add_parser.add_argument("--yes", "-y", action="store_true",
                           help="Auto-accept fingerprint without confirmation")

    # remove
    remove_parser = subparsers.add_parser("remove", help="Remove a server")
    remove_parser.add_argument("name", help="Server alias name to remove")

    # list
    subparsers.add_parser("list", help="List all servers")

    args = parser.parse_args()

    if args.action == "add":
        # Interactive password input (hidden)
        print(f"正在添加服务器: {args.name} ({args.ip})")
        print(f"用户: {args.user}, 端口: {args.port}")
        password = getpass.getpass("请输入密码: ")

        if not password:
            print("错误: 密码不能为空")
            sys.exit(1)

        # Create manager after password input
        manager = ServerManager(config_path=args.config_path)
        server_config: ServerAddConfig = {
            "name": args.name,
            "ip": args.ip,
            "port": args.port,
            "user": args.user,
            "password": password
        }

        print("\n正在获取服务器指纹...")
        fp_result = manager.client.get_server_fingerprint(server_config)

        if fp_result["status"] != "success":
            print(f"警告: 无法获取服务器指纹: {fp_result['message']}")
            print("将使用不安全的自动接受策略连接")
            verified_host_key = None
        else:
            fp_data = fp_result.get("data", {})
            fingerprint_display = fp_result["stdout"]
            print(f"\n服务器指纹信息:")
            print(f"  IP: {args.ip}")
            print(f"  端口: {args.port}")
            print(f"  指纹: {fingerprint_display}")
            print()

            # Ask user to confirm fingerprint
            if args.yes:
                print("自动接受指纹 (--yes)")
                verified_host_key = fp_data.get("host_key")
            else:
                while True:
                    confirm = input("请确认上述指纹是否正确? [y/N]: ").strip().lower()
                    if confirm in ('y', 'yes'):
                        verified_host_key = fp_data.get("host_key")
                        break
                    elif confirm in ('n', 'no', ''):
                        print("用户取消操作")
                        sys.exit(0)
                    else:
                        print("请输入 y 或 n")

            # Add verified host key to known_hosts
            if verified_host_key:
                success, msg = add_to_known_hosts(args.ip, args.port, verified_host_key)
                if success:
                    print(f"指纹已保存到: {get_known_hosts_path()}")
                else:
                    print(f"警告: {msg}")

        # Proceed with server addition
        result = manager.add_server(
            name=args.name,
            ip=args.ip,
            password=password,
            port=args.port,
            user=args.user,
            key_path=args.key_path,
            verified_host_key=verified_host_key
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if result["status"] == "error":
            sys.exit(1)

    elif args.action == "remove":
        manager = ServerManager(config_path=args.config_path)
        result = manager.remove_server(args.name)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if result["status"] == "error":
            sys.exit(1)

    elif args.action == "list":
        manager = ServerManager(config_path=args.config_path)
        result = manager.list_servers()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()