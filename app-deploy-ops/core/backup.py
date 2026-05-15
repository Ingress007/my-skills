"""服务器备份管理 - 在远程服务器上备份应用包和配置文件"""

from datetime import datetime


class BackupManager:
    """管理远程服务器上的备份操作"""

    def __init__(self, ssh_client, env: str):
        self.ssh = ssh_client
        self.app_dir = f"/opt/apps/{env}"

    def backup_app(self, service_name: str = "app") -> str:
        """备份远程服务器上的应用包

        Args:
            service_name: 服务名称

        Returns:
            备份文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        app_path = f"{self.app_dir}/backend/services/{service_name}/app.jar"
        backup_dir = f"{self.app_dir}/backup/app"
        backup_file = f"{backup_dir}/{service_name}.jar.{timestamp}.bak"

        # 检查源文件是否存在
        stdin, stdout, stderr = self.ssh.exec_command(
            f"test -f {app_path} && echo 'EXISTS' || echo 'NOT_EXISTS'")
        result = stdout.read().decode().strip()

        if result != "EXISTS":
            print(f"[Backup] 应用包不存在: {app_path}")
            return ""

        # 创建备份目录并备份
        commands = f"""
mkdir -p {backup_dir}
cp {app_path} {backup_file}
echo 'OK'
        """
        stdin, stdout, stderr = self.ssh.exec_command(commands.strip())
        output = stdout.read().decode().strip()

        if "OK" in output:
            print(f"[Backup] 应用包备份完成: {backup_file}")
            return backup_file
        else:
            print(f"[Backup] 备份失败: {stderr.read().decode().strip()}")
            return ""

    def backup_config(self, config_path: str) -> str:
        """备份远程服务器上的配置文件

        Args:
            config_path: 配置文件路径

        Returns:
            备份文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"{self.app_dir}/backup/config"
        filename = config_path.replace("/", "_") + f".{timestamp}.bak"
        backup_file = f"{backup_dir}/{filename}"

        # 检查源文件是否存在
        stdin, stdout, stderr = self.ssh.exec_command(
            f"test -f {config_path} && echo 'EXISTS' || echo 'NOT_EXISTS'")
        result = stdout.read().decode().strip()

        if result != "EXISTS":
            print(f"[Backup] 配置文件不存在: {config_path}")
            return ""

        commands = f"""
mkdir -p {backup_dir}
cp {config_path} {backup_file}
echo 'OK'
        """
        stdin, stdout, stderr = self.ssh.exec_command(commands.strip())
        output = stdout.read().decode().strip()

        if "OK" in output:
            print(f"[Backup] 配置备份完成: {backup_file}")
            return backup_file
        else:
            print(f"[Backup] 备份失败: {stderr.read().decode().strip()}")
            return ""

    def list_backups(self, backup_type: str = "app") -> list:
        """列出备份文件

        Args:
            backup_type: app/config/db

        Returns:
            备份文件列表
        """
        backup_dir = f"{self.app_dir}/backup/{backup_type}"
        stdin, stdout, stderr = self.ssh.exec_command(
            f"ls -1t {backup_dir} 2>/dev/null || echo 'NO_BACKUPS'")
        output = stdout.read().decode().strip().split("\n")

        if output[0] == "NO_BACKUPS":
            return []

        return output

    def cleanup_old(self, backup_type: str = "app", keep: int = 10):
        """清理旧备份，保留指定数量

        Args:
            backup_type: app/config/db
            keep: 保留数量
        """
        backups = self.list_backups(backup_type)
        if len(backups) <= keep:
            return

        to_delete = backups[keep:]
        backup_dir = f"{self.app_dir}/backup/{backup_type}"
        for filename in to_delete:
            self.ssh.exec_command(f"rm -f {backup_dir}/{filename}")
            print(f"[Backup] 清理旧备份: {filename}")