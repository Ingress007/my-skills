"""Systemd 操作 - 远程 systemd 服务管理"""


class SystemdManager:
    """远程 systemd 服务管理"""

    def __init__(self, ssh_client):
        self.ssh = ssh_client

    def daemon_reload(self) -> str:
        """重新加载 systemd 配置"""
        stdin, stdout, stderr = self.ssh.exec_command("systemctl daemon-reload")
        return stdout.read().decode().strip()

    def restart(self, service_name: str) -> dict:
        """重启服务

        Args:
            service_name: 服务名称

        Returns:
            操作结果
        """
        cmd = f"systemctl restart {service_name} 2>&1 && echo 'OK' || echo 'FAIL'"
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        output = stdout.read().decode().strip()

        success = "OK" in output
        return {
            "service": service_name,
            "success": success,
            "output": output,
        }

    def stop(self, service_name: str) -> dict:
        """停止服务"""
        cmd = f"systemctl stop {service_name} 2>&1 && echo 'OK' || echo 'FAIL'"
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        output = stdout.read().decode().strip()
        return {"service": service_name, "success": "OK" in output}

    def start(self, service_name: str) -> dict:
        """启动服务"""
        cmd = f"systemctl start {service_name} 2>&1 && echo 'OK' || echo 'FAIL'"
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        output = stdout.read().decode().strip()
        return {"service": service_name, "success": "OK" in output}

    def status(self, service_name: str) -> dict:
        """查看服务状态"""
        cmd = f"systemctl is-active {service_name} 2>/dev/null"
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        active = stdout.read().decode().strip()

        cmd = f"systemctl is-enabled {service_name} 2>/dev/null"
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        enabled = stdout.read().decode().strip()

        # 获取进程 PID
        cmd = f"systemctl show -p MainPID {service_name} 2>/dev/null | cut -d= -f2"
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        pid = stdout.read().decode().strip()

        return {
            "service": service_name,
            "active": active,
            "enabled": enabled,
            "pid": pid if pid and pid != "0" else "",
        }