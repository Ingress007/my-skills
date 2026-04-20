"""
Public type definitions for my-skills project.
"""
from typing import TypedDict, Optional


class SSHServerConfig(TypedDict, total=False):
    """SSH server configuration from .ssh/config"""
    hostname: str
    user: Optional[str]
    port: int
    identityfile: Optional[str]


class SSHResult(TypedDict):
    """SSH command execution result"""
    status: str  # 'success' | 'error'
    stdout: str
    stderr: str
    exit_code: int
    message: Optional[str]  # Only present when status='error'


class CommandCheckResult(TypedDict):
    """Command safety check result"""
    allowed: bool
    requires_confirmation: bool
    reason: str