"""
SSH Config Parser - Parse OpenSSH config file format
"""
import os
import re
from pathlib import Path
from typing import Dict, Optional, List


def get_ssh_config_path() -> str:
    """Get the default SSH config file path."""
    if os.name == 'nt':
        # Windows
        home = os.environ.get('USERPROFILE', os.path.expanduser('~'))
        return os.path.join(home, '.ssh', 'config')
    else:
        # Unix-like
        return os.path.expanduser('~/.ssh/config')


def get_ssh_dir() -> str:
    """Get the default SSH directory path."""
    if os.name == 'nt':
        home = os.environ.get('USERPROFILE', os.path.expanduser('~'))
        return os.path.join(home, '.ssh')
    else:
        return os.path.expanduser('~/.ssh')


def parse_ssh_config(config_path: Optional[str] = None) -> Dict[str, Dict[str, Optional[str | int]]]:
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

    hosts: Dict[str, Dict[str, Optional[str | int]]] = {}
    current_host: Optional[str] = None

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


def get_host_config(alias: str, config_path: Optional[str] = None) -> Optional[Dict[str, Optional[str | int]]]:
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


def list_hosts(config_path: Optional[str] = None) -> List[str]:
    """
    List all host aliases from SSH config.

    Args:
        config_path: Path to SSH config file. If None, uses default location.

    Returns:
        list: List of host aliases
    """
    hosts = parse_ssh_config(config_path)
    return list(hosts.keys())


def host_exists(alias: str, config_path: Optional[str] = None) -> bool:
    """
    Check if a host alias exists in SSH config.

    Args:
        alias: Host alias to check
        config_path: Path to SSH config file. If None, uses default location.

    Returns:
        bool: True if host exists
    """
    hosts = parse_ssh_config(config_path)
    return alias in hosts


def generate_unique_name(base_name: str, config_path: Optional[str] = None) -> str:
    """
    Generate a unique host name by adding a number suffix if name already exists.

    Args:
        base_name: Base name for the host
        config_path: Path to SSH config file. If None, uses default location.

    Returns:
        str: Unique host name
    """
    hosts = parse_ssh_config(config_path)
    
    if base_name not in hosts:
        return base_name
    
    # Find next available number
    counter = 1
    while f"{base_name}-{counter}" in hosts:
        counter += 1
    
    return f"{base_name}-{counter}"


def add_host(
    host: str,
    hostname: str,
    user: str = "root",
    port: int = 22,
    identityfile: Optional[str] = None,
    config_path: Optional[str] = None
) -> bool:
    """
    Add a new host entry to SSH config file.

    Args:
        host: Host alias name
        hostname: Server IP or hostname
        user: SSH username (default root)
        port: SSH port (default 22)
        identityfile: Path to private key file
        config_path: Path to SSH config file. If None, uses default location.

    Returns:
        bool: True if successfully added
    """
    if config_path is None:
        config_path = get_ssh_config_path()
    
    # Ensure SSH directory exists
    ssh_dir = os.path.dirname(config_path)
    if not os.path.exists(ssh_dir):
        os.makedirs(ssh_dir, mode=0o700)
    
    # Build host entry
    entry_lines = [f"Host {host}"]
    entry_lines.append(f"    HostName {hostname}")
    entry_lines.append(f"    User {user}")
    entry_lines.append(f"    Port {port}")
    if identityfile:
        # Use relative path with ~ for portability
        # Use prefix truncation (not str.replace) to avoid replacing occurrences
        # of home path that may appear elsewhere in the path string
        home = os.environ.get('USERPROFILE', os.path.expanduser('~')) if os.name == 'nt' else os.path.expanduser('~')
        if identityfile.startswith(home):
            identityfile = '~' + identityfile[len(home):]
        entry_lines.append(f"    IdentityFile {identityfile}")
    
    entry = "\n" + "\n".join(entry_lines) + "\n"
    
    # Check if config file exists
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        content += entry
    else:
        content = entry
    
    # Write config file
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(content)
        # Set proper permissions for SSH config file
        os.chmod(config_path, 0o600)
        return True
    except IOError:
        return False


def remove_host(alias: str, config_path: Optional[str] = None) -> bool:
    """
    Remove a host entry from SSH config file.

    Args:
        alias: Host alias to remove
        config_path: Path to SSH config file. If None, uses default location.

    Returns:
        bool: True if successfully removed, False if host not found
    """
    if config_path is None:
        config_path = get_ssh_config_path()
    
    if not os.path.exists(config_path):
        return False
    
    with open(config_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find and remove host block
    new_lines = []
    in_target_host = False
    found = False
    host_pattern = re.compile(r'^Host\s+', re.IGNORECASE)

    for line in lines:
        stripped = line.strip()

        # Check for Host line
        if host_pattern.match(stripped):
            host_names = stripped[5:].strip().split()
            if host_names[0] == alias:
                in_target_host = True
                found = True
                continue  # Skip this Host line
            else:
                in_target_host = False

        # Skip all lines within target host block (until next Host line)
        if in_target_host:
            continue

        new_lines.append(line)

    # Host alias not found in config, nothing was removed
    if not found:
        return False

    # Write back
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        # Set proper permissions
        os.chmod(config_path, 0o600)
        return True
    except IOError:
        return False
