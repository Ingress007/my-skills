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


class ServerAddConfig(TypedDict):
    """Server configuration for adding new host"""
    name: str          # Server alias name (unique)
    ip: str            # Server IP address
    port: int          # SSH port (default 22)
    user: str          # SSH username (default root)
    password: str      # Password (one-time use, not saved)


class SSHConfigEntry(TypedDict, total=False):
    """SSH config entry for writing to config file"""
    host: str                    # Host alias
    hostname: str                # Server IP or hostname
    user: str                    # SSH username
    port: int                    # SSH port
    identityfile: Optional[str]  # Path to private key (optional)
