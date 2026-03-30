"""
SSH Config Parser - Parse OpenSSH config file format
"""
import os
import re
from pathlib import Path


def get_ssh_config_path():
    """Get the default SSH config file path."""
    if os.name == 'nt':
        # Windows
        home = os.environ.get('USERPROFILE', os.path.expanduser('~'))
        return os.path.join(home, '.ssh', 'config')
    else:
        # Unix-like
        return os.path.expanduser('~/.ssh/config')


def parse_ssh_config(config_path=None):
    """
    Parse SSH config file and return a dict of host configurations.

    Args:
        config_path: Path to SSH config file. If None, uses default location.

    Returns:
        dict: {host_alias: {hostname, user, port, identityfile}}
    """
    if config_path is None:
        config_path = get_ssh_config_path()

    if not os.path.exists(config_path):
        return {}

    hosts = {}
    current_host = None

    with open(config_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            # Parse Host line
            if line.lower().startswith('host '):
                # Get host name(s) - can be multiple, separated by space
                host_names = line[5:].strip().split()
                # Use the first host name as the alias
                current_host = host_names[0]
                hosts[current_host] = {
                    'hostname': current_host,  # Default to alias if no HostName specified
                    'user': None,
                    'port': 22,
                    'identityfile': None
                }
                continue

            # Parse other directives
            if current_host is None:
                continue

            # Handle key-value pairs (case-insensitive keys)
            parts = line.split(None, 1)
            if len(parts) == 2:
                key = parts[0].lower()
                value = parts[1]

                if key == 'hostname':
                    hosts[current_host]['hostname'] = value
                elif key == 'user':
                    hosts[current_host]['user'] = value
                elif key == 'port':
                    hosts[current_host]['port'] = int(value)
                elif key == 'identityfile':
                    # Expand ~ to home directory
                    expanded_path = os.path.expanduser(value)
                    hosts[current_host]['identityfile'] = expanded_path

    return hosts


def get_host_config(alias, config_path=None):
    """
    Get configuration for a specific host alias.

    Args:
        alias: Host alias from SSH config
        config_path: Path to SSH config file. If None, uses default location.

    Returns:
        dict: {hostname, user, port, identityfile} or None if not found
    """
    hosts = parse_ssh_config(config_path)
    return hosts.get(alias)


def list_hosts(config_path=None):
    """
    List all host aliases from SSH config.

    Args:
        config_path: Path to SSH config file. If None, uses default location.

    Returns:
        list: List of host aliases
    """
    hosts = parse_ssh_config(config_path)
    return list(hosts.keys())