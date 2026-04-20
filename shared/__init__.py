"""
Shared modules for my-skills project.
Provides common SSH client, config parser, and type definitions.
"""

from .ssh_client import SSHClient, create_ssh_client, DEFAULT_TIMEOUT
from .ssh_config_parser import parse_ssh_config, get_host_config, list_hosts, get_ssh_config_path

# 注意：不直接导出 types 模块以避免与标准库冲突
# 使用方式：from shared.type_defs import SSHServerConfig, SSHResult

__all__ = [
    'SSHClient',
    'create_ssh_client',
    'DEFAULT_TIMEOUT',
    'parse_ssh_config',
    'get_host_config',
    'list_hosts',
    'get_ssh_config_path',
]