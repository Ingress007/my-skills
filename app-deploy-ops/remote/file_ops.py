"""远程文件操作 - 文件上传下载"""

import os
import tempfile


class FileManager:
    """远程文件管理"""

    def __init__(self, ssh_client):
        self.ssh = ssh_client
        self.sftp = ssh_client.get_sftp() if hasattr(ssh_client, 'get_sftp') else None

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """上传文件到远程服务器

        Args:
            local_path: 本地文件路径
            remote_path: 远程目标路径

        Returns:
            是否成功
        """
        if not os.path.exists(local_path):
            print(f"[File] 本地文件不存在: {local_path}")
            return False

        try:
            if self.sftp:
                # 确保远程目录存在
                remote_dir = os.path.dirname(remote_path)
                self.ssh.exec_command(f"mkdir -p {remote_dir}")
                self.sftp.put(local_path, remote_path)
                print(f"[File] 上传完成: {local_path} -> {remote_path}")
                return True
            else:
                print("[File] SFTP 不可用，使用 scp 方式")
                return self._upload_via_scp(local_path, remote_path)
        except Exception as e:
            print(f"[File] 上传失败: {e}")
            return False

    def upload_dir(self, local_dir: str, remote_dir: str) -> bool:
        """上传目录到远程服务器"""
        if not os.path.isdir(local_dir):
            print(f"[File] 本地目录不存在: {local_dir}")
            return False

        try:
            self.ssh.exec_command(f"mkdir -p {remote_dir}")
            for root, dirs, files in os.walk(local_dir):
                for file in files:
                    local_file = os.path.join(root, file)
                    rel_path = os.path.relpath(local_file, local_dir)
                    remote_file = os.path.join(remote_dir, rel_path).replace("\\", "/")

                    remote_file_dir = os.path.dirname(remote_file)
                    self.ssh.exec_command(f"mkdir -p {remote_file_dir}")

                    if self.sftp:
                        self.sftp.put(local_file, remote_file)
                    else:
                        self._upload_via_scp(local_file, remote_file)

            print(f"[File] 目录上传完成: {local_dir} -> {remote_dir}")
            return True
        except Exception as e:
            print(f"[File] 目录上传失败: {e}")
            return False

    def download_file(self, remote_path: str, local_path: str) -> bool:
        """从远程服务器下载文件"""
        try:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            if self.sftp:
                self.sftp.get(remote_path, local_path)
                print(f"[File] 下载完成: {remote_path} -> {local_path}")
                return True
            else:
                return self._download_via_scp(remote_path, local_path)
        except Exception as e:
            print(f"[File] 下载失败: {e}")
            return False

    def set_permissions(self, remote_path: str, mode: str = "600") -> bool:
        """设置远程文件权限"""
        cmd = f"chmod {mode} {remote_path} && echo 'OK'"
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        return "OK" in stdout.read().decode().strip()

    def _upload_via_scp(self, local_path: str, remote_path: str) -> bool:
        """通过 scp 命令上传"""
        import subprocess
        host = self.ssh._hostname if hasattr(self.ssh, '_hostname') else "host"
        cmd = f"scp -o StrictHostKeyChecking=no {local_path} {host}:{remote_path}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0

    def _download_via_scp(self, remote_path: str, local_path: str) -> bool:
        """通过 scp 命令下载"""
        import subprocess
        host = self.ssh._hostname if hasattr(self.ssh, '_hostname') else "host"
        cmd = f"scp -o StrictHostKeyChecking=no {host}:{remote_path} {local_path}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0