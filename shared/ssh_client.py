"""
SSH Client - Common SSH connection module
Shared by linux-ops, docker-ops, and rocketmq-ops.
"""
import paramiko
import hashlib
import base64
from typing import Optional, Dict, Any, Tuple

# 使用绝对导入，避免相对导入问题
import sys
import os
_type_defs_path = os.path.dirname(os.path.abspath(__file__))
if _type_defs_path not in sys.path:
    sys.path.insert(0, _type_defs_path)
from type_defs import SSHServerConfig, SSHResult, ServerAddConfig

# Default timeout (seconds)
DEFAULT_TIMEOUT = 10


def get_known_hosts_path() -> str:
    """Get the default known_hosts file path."""
    if os.name == 'nt':
        home = os.environ.get('USERPROFILE', os.path.expanduser('~'))
        return os.path.join(home, '.ssh', 'known_hosts')
    else:
        return os.path.expanduser('~/.ssh/known_hosts')


def get_host_key_entry(ip: str, port: int, host_key: paramiko.PKey) -> str:
    """
    Generate known_hosts entry for a host key.

    Args:
        ip: Server IP address
        port: SSH port
        host_key: Host key object

    Returns:
        str: known_hosts format entry
    """
    if port == 22:
        host_line = ip
    else:
        host_line = f"[{ip}]:{port}"

    key_type = host_key.get_name()
    key_base64 = host_key.asbytes()

    key_b64 = base64.b64encode(key_base64).decode('utf-8')

    return f"{host_line} {key_type} {key_b64}"


def add_to_known_hosts(ip: str, port: int, host_key: paramiko.PKey) -> Tuple[bool, str]:
    """
    Add server host key to known_hosts file.

    Args:
        ip: Server IP address
        port: SSH port
        host_key: Host key object from paramiko

    Returns:
        tuple: (success, message)
    """
    known_hosts_path = get_known_hosts_path()

    # Ensure .ssh directory exists
    ssh_dir = os.path.dirname(known_hosts_path)
    if not os.path.exists(ssh_dir):
        try:
            os.makedirs(ssh_dir, mode=0o700)
        except OSError as e:
            return False, f"Failed to create SSH directory: {str(e)}"

    # Generate entry
    entry = get_host_key_entry(ip, port, host_key)

    # Check if entry already exists
    if os.path.exists(known_hosts_path):
        with open(known_hosts_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if entry in content:
            return True, f"Host key already in known_hosts"
        content += '\n' + entry
    else:
        content = entry

    # Write to known_hosts
    try:
        with open(known_hosts_path, 'w', encoding='utf-8') as f:
            f.write(content)
        os.chmod(known_hosts_path, 0o600)
        return True, f"Added to known_hosts: {known_hosts_path}"
    except IOError as e:
        return False, f"Failed to write known_hosts: {str(e)}"


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

    def connect_with_password(
        self,
        server: ServerAddConfig,
        verified_host_key: Optional[paramiko.PKey] = None
    ) -> SSHResult:
        """
        Connect to server using password authentication.

        Args:
            server: Server configuration with password
            verified_host_key: Pre-verified host key (optional, for secure connection)

        Returns:
            SSHResult with connection test result
        """
        client = paramiko.SSHClient()

        # Use secure policy if host key is verified, otherwise use AutoAddPolicy
        if verified_host_key:
            client.get_host_keys().add(
                f"[{server['ip']}]:{server['port']}" if server['port'] != 22 else server['ip'],
                verified_host_key.get_name(),
                verified_host_key
            )
            # Reject connection if actual host key doesn't match verified key
            client.set_missing_host_key_policy(paramiko.RejectPolicy())
        else:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            client.connect(
                hostname=server["ip"],
                port=server["port"],
                username=server["user"],
                password=server["password"],
                timeout=self.timeout
            )

            # Test connection with simple command
            stdin, stdout, stderr = client.exec_command("echo 'connection_test_ok'")
            exit_code = stdout.channel.recv_exit_status()
            out = stdout.read().decode('utf-8', errors='replace')

            if exit_code == 0 and 'connection_test_ok' in out:
                return {
                    "status": "success",
                    "stdout": out,
                    "stderr": "",
                    "exit_code": 0,
                    "message": None
                }
            else:
                return {
                    "status": "error",
                    "stdout": out,
                    "stderr": stderr.read().decode('utf-8', errors='replace'),
                    "exit_code": exit_code,
                    "message": "Connection test failed"
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

    def _execute_command(
        self,
        client: paramiko.SSHClient,
        command: str
    ) -> SSHResult:
        """
        Execute a command on an already-connected SSH client.

        Args:
            client: Connected paramiko SSHClient
            command: Command string to execute

        Returns:
            SSHResult with execution result
        """
        try:
            stdin, stdout, stderr = client.exec_command(command)
            exit_code = stdout.channel.recv_exit_status()
            err = stderr.read().decode('utf-8', errors='replace')

            if exit_code != 0:
                return {
                    "status": "error",
                    "stdout": "",
                    "stderr": err,
                    "exit_code": exit_code,
                    "message": f"Failed to execute: {command}"
                }

            return {
                "status": "success",
                "stdout": stdout.read().decode('utf-8', errors='replace'),
                "stderr": err,
                "exit_code": 0,
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

    def upload_ssh_key(
        self,
        server: ServerAddConfig,
        public_key: str,
        verified_host_key: Optional[paramiko.PKey] = None
    ) -> SSHResult:
        """
        Upload SSH public key to remote server's authorized_keys.

        Args:
            server: Server configuration with password
            public_key: SSH public key content
            verified_host_key: Pre-verified host key (optional, for secure connection)

        Returns:
            SSHResult with upload result
        """
        client = paramiko.SSHClient()

        # Use secure policy if host key is verified, otherwise use AutoAddPolicy
        if verified_host_key:
            client.get_host_keys().add(
                f"[{server['ip']}]:{server['port']}" if server['port'] != 22 else server['ip'],
                verified_host_key.get_name(),
                verified_host_key
            )
            # Reject connection if actual host key doesn't match verified key
            client.set_missing_host_key_policy(paramiko.RejectPolicy())
        else:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            client.connect(
                hostname=server["ip"],
                port=server["port"],
                username=server["user"],
                password=server["password"],
                timeout=self.timeout
            )
            
            # Ensure .ssh directory exists with correct permissions
            mkdir_result = self._execute_command(client, "mkdir -p ~/.ssh && chmod 700 ~/.ssh")
            if mkdir_result["status"] == "error":
                return mkdir_result

            # Safely write public key using stdin (avoid command injection)
            # Read key from stdin into shell variable, then do exact-line dedup check
            # before appending, to avoid duplicate entries on retries
            stdin, stdout, stderr = client.exec_command(
                'key=$(cat); grep -qxF -- "$key" ~/.ssh/authorized_keys 2>/dev/null'
                ' || printf \'%s\\n\' "$key" >> ~/.ssh/authorized_keys'
            )
            stdin.write(public_key)
            stdin.flush()
            stdin.channel.shutdown_write()

            exit_code = stdout.channel.recv_exit_status()
            if exit_code != 0:
                err = stderr.read().decode('utf-8', errors='replace')
                return {
                    "status": "error",
                    "stdout": "",
                    "stderr": err,
                    "exit_code": exit_code,
                    "message": "Failed to write public key to authorized_keys"
                }

            chmod_result = self._execute_command(client, "chmod 600 ~/.ssh/authorized_keys")
            if chmod_result["status"] == "error":
                return chmod_result
            
            return {
                "status": "success",
                "stdout": "SSH public key uploaded successfully",
                "stderr": "",
                "exit_code": 0,
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

    def get_server_fingerprint(
        self,
        server: ServerAddConfig
    ) -> SSHResult:
        """
        Get server SSH fingerprint for verification.
        This connects to the server to retrieve its host key without verifying it.

        Args:
            server: Server configuration

        Returns:
            SSHResult with fingerprint info and host_key in 'data' field
        """
        transport = None
        try:
            # Create transport and connect to get host key
            transport = paramiko.Transport((server["ip"], server["port"]))
            transport.start_client()

            # Get host key (this works regardless of known_hosts)
            host_key = transport.get_remote_server_key()
            # Compute SHA256 fingerprint (matches ssh-keygen -l output format)
            fingerprint_bytes = hashlib.sha256(host_key.asbytes()).digest()
            fingerprint = base64.b64encode(fingerprint_bytes).decode('utf-8').rstrip('=')
            key_type = host_key.get_name()

            return {
                "status": "success",
                "stdout": f"{key_type} SHA256:{fingerprint}",
                "stderr": "",
                "exit_code": 0,
                "message": None,
                "data": {
                    "host_key": host_key,
                    "key_type": key_type,
                    "fingerprint": fingerprint,
                    "ip": server["ip"],
                    "port": server["port"]
                }
            }

        except paramiko.SSHException as e:
            # Handle SSH-specific errors (like host key verification)
            return {
                "status": "error",
                "stdout": "",
                "stderr": "",
                "exit_code": -1,
                "message": f"SSH error: {str(e)}"
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
            if transport:
                transport.close()

    def test_key_auth(
        self,
        server: SSHServerConfig
    ) -> SSHResult:
        """
        Test SSH key authentication after key upload.
        
        Args:
            server: SSH server configuration with identityfile
            
        Returns:
            SSHResult with test result
        """
        return self.execute(server, "echo 'key_auth_test_ok'")


def create_ssh_client(timeout: Optional[int] = None) -> SSHClient:
    """
    Create an SSHClient instance.

    Args:
        timeout: Optional timeout override

    Returns:
        SSHClient instance
    """
    return SSHClient(timeout=timeout or DEFAULT_TIMEOUT)