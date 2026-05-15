"""SSH 操作封装 - 基于 shared/ssh_client.py"""

import sys
import os

# 添加项目根路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from shared.ssh_client import SSHClient
from shared.ssh_config_parser import SSHConfigParser
from shared.type_defs import ServerInfo


class SSHConnectionError(Exception):
    """SSH 连接异常"""
    pass


class SSHAuthError(Exception):
    """SSH 认证异常"""
    pass


class SSHManager:
    """SSH 连接管理"""

    def __init__(self):
        self._client = None
        self._server_info = None

    def connect(self, server_name: str) -> SSHClient:
        """通过 SSH config 中的服务器名连接

        Args:
            server_name: SSH config 中的 Host 名称

        Returns:
            SSHClient 实例
        """
        parser = SSHConfigParser()
        config = parser.parse()

        server_info = config.get(server_name)
        if not server_info:
            available = list(config.keys())
            raise SSHConnectionError(
                f"服务器 '{server_name}' 未在 ~/.ssh/config 中配置。"
                f"可用服务器: {available}"
            )

        self._server_info = server_info

        client = SSHClient(
            hostname=server_info.hostname,
            port=server_info.port,
            username=server_info.username,
            key_filename=server_info.identity_file,
            timeout=10,
        )
        client.connect()

        self._client = client
        return client

    def disconnect(self):
        """断开 SSH 连接"""
        if self._client:
            self._client.close()
            self._client = None

    @property
    def client(self) -> SSHClient:
        return self._client

    @property
    def server_info(self):
        return self._server_info