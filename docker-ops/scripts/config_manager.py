"""
Docker Config Manager - Manage Docker command safety blacklist
"""
import json
import os
import re
import sys
from typing import Dict, List, Tuple, Optional, Any

# Import from shared module
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_shared_path = os.path.join(_project_root, "shared")
sys.path.insert(0, _shared_path)

from ssh_config_parser import get_host_config, list_hosts
from type_defs import SSHServerConfig

CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
BLACKLIST_FILE = os.path.join(CONFIG_DIR, 'blacklist.json')


class ConfigManager:
    def __init__(self) -> None:
        self._load_blacklist()

    def _load_blacklist(self) -> None:
        """Load Docker command blacklist patterns."""
        if os.path.exists(BLACKLIST_FILE):
            with open(BLACKLIST_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.blacklist: List[str] = data.get("blacklist", [])
                self.confirm_patterns: List[str] = data.get("confirm_patterns", [])
        else:
            # Default Docker safety patterns
            self.blacklist = [
                r"^docker\s+system\s+prune\s+-af",
                r"^docker\s+rm\s+-f.*\$\(\s*docker",
                r"^docker\s+rmi.*\$\(\s*docker"
            ]
            self.confirm_patterns = [
                r"^docker\s+(stop|restart|rm|rmi|push|build)",
                r"^docker\s+system\s+prune",
                r"^docker\s+compose\s+(up|down|restart|build)"
            ]
            self._save_blacklist()

    def _save_blacklist(self) -> None:
        """Save blacklist to file."""
        with open(BLACKLIST_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                "blacklist": self.blacklist,
                "confirm_patterns": self.confirm_patterns
            }, f, indent=4)

    def get_server(self, alias: str) -> Optional[SSHServerConfig]:
        """
        Get server configuration from SSH config.

        Args:
            alias: Host alias from SSH config file

        Returns:
            dict: {hostname, user, port, identityfile} or None if not found
        """
        config = get_host_config(alias)
        if config:
            return {
                "hostname": config.get("hostname", alias),
                "user": config.get("user"),
                "port": config.get("port", 22),
                "identityfile": config.get("identityfile")
            }
        return None

    def list_servers(self) -> List[str]:
        """
        List all host aliases from SSH config.

        Returns:
            list: List of host aliases
        """
        return list_hosts()

    def check_command(self, command: str) -> Tuple[bool, bool, str]:
        """
        Check if a Docker command is allowed and whether it requires confirmation.

        Returns:
            tuple: (allowed, requires_confirmation, reason)
        """
        for pattern in self.blacklist:
            if re.search(pattern, command):
                return False, False, f"Command matches blacklist pattern: {pattern}"

        for pattern in self.confirm_patterns:
            if re.search(pattern, command):
                return True, True, f"Command matches confirmation pattern: {pattern}"

        return True, False, "OK"