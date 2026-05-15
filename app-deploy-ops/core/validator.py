"""验证检查 - 部署前后的验证工具"""

import socket


class Validator:
    """部署验证工具"""

    @staticmethod
    def check_port(host: str, port: int, timeout: int = 5) -> bool:
        """检查远程端口是否可达"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            result = sock.connect_ex((host, port))
            return result == 0
        finally:
            sock.close()

    @staticmethod
    def check_health(host: str, port: int, path: str = "/actuator/health",
                     timeout: int = 10) -> dict:
        """HTTP 健康检查"""
        import urllib.request
        import json

        url = f"http://{host}:{port}{path}"
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode()
                status = resp.status
                data = json.loads(body) if body else {}
                return {
                    "url": url,
                    "status_code": status,
                    "healthy": status == 200,
                    "body": data,
                }
        except Exception as e:
            return {
                "url": url,
                "healthy": False,
                "error": str(e),
            }

    @staticmethod
    def validate_process(ssh_client, process_name: str) -> dict:
        """通过 SSH 检查远程进程状态"""
        cmd = f"ps aux | grep -v grep | grep '{process_name}' | head -5"
        stdin, stdout, stderr = ssh_client.exec_command(cmd)
        output = stdout.read().decode().strip()

        if output:
            return {
                "running": True,
                "processes": output.split("\n"),
            }
        return {
            "running": False,
            "processes": [],
        }