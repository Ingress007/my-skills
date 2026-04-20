"""
SSH Client - Common SSH connection module
Shared by linux-ops, docker-ops, and rocketmq-ops.
"""
import paramiko
from typing import Optional, Dict, Any

# 使用绝对导入，避免相对导入问题
import sys
import os
_type_defs_path = os.path.dirname(os.path.abspath(__file__))
if _type_defs_path not in sys.path:
    sys.path.insert(0, _type_defs_path)
from type_defs import SSHServerConfig, SSHResult

# Default timeout (seconds)
DEFAULT_TIMEOUT = 10


class SSHClient:
    """SSH connection client wrapper"""

    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        """
        Initialize SSH client.

        Args:
            timeout: Connection timeout in seconds
        """
        self.timeout = timeout

    def execute(
        self,
        server: SSHServerConfig,
        command: str
    ) -> SSHResult:
        """
        Execute a command on remote server.

        Args:
            server: SSH server configuration dict
            command: Command string to execute

        Returns:
            SSHResult with status, stdout, stderr, exit_code
        """
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            connect_kwargs: Dict[str, Any] = {
                "hostname": server["hostname"],
                "port": int(server.get("port", 22)),
                "username": server.get("user") or "root",
                "timeout": self.timeout
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
                "exit_code": exit_code,
                "message": None
            }

        except Exception as e:
            return {
                "status": "error",
                "stdout": "",
                "stderr": "",
                "exit_code": -1,
                "message": str(e)
            }
        finally:
            client.close()

    def execute_script(
        self,
        server: SSHServerConfig,
        script_content: str
    ) -> SSHResult:
        """
        Execute script content on remote server via bash -s.

        Args:
            server: SSH server configuration dict
            script_content: Script content string

        Returns:
            SSHResult with execution result
        """
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            connect_kwargs: Dict[str, Any] = {
                "hostname": server["hostname"],
                "port": int(server.get("port", 22)),
                "username": server.get("user") or "root",
                "timeout": self.timeout
            }

            if server.get("identityfile"):
                connect_kwargs["key_filename"] = server["identityfile"]

            client.connect(**connect_kwargs)

            stdin, stdout, stderr = client.exec_command("bash -s")
            stdin.write(script_content)
            stdin.flush()
            stdin.channel.shutdown_write()

            exit_code = stdout.channel.recv_exit_status()
            out = stdout.read().decode('utf-8', errors='replace')
            err = stderr.read().decode('utf-8', errors='replace')

            return {
                "status": "success",
                "stdout": out,
                "stderr": err,
                "exit_code": exit_code,
                "message": None
            }

        except Exception as e:
            return {
                "status": "error",
                "stdout": "",
                "stderr": "",
                "exit_code": -1,
                "message": str(e)
            }
        finally:
            client.close()

    def execute_script_file(
        self,
        server: SSHServerConfig,
        script_path: str
    ) -> SSHResult:
        """
        Execute a local script file on remote server.

        Args:
            server: SSH server configuration dict
            script_path: Local script file path

        Returns:
            SSHResult with execution result
        """
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()
        except Exception as e:
            return {
                "status": "error",
                "stdout": "",
                "stderr": "",
                "exit_code": -1,
                "message": f"Failed to read script: {str(e)}"
            }

        return self.execute_script(server, script_content)


def create_ssh_client(timeout: Optional[int] = None) -> SSHClient:
    """
    Create an SSHClient instance.

    Args:
        timeout: Optional timeout override

    Returns:
        SSHClient instance
    """
    return SSHClient(timeout=timeout or DEFAULT_TIMEOUT)