"""
Docker Config Manager - Manage Docker command safety blacklist
"""
import json
import os
import re
import sys

# Import SSH config parser from linux-ops
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_current_dir))
linux_ops_path = os.path.join(_project_root, "linux-ops", "scripts")
sys.path.insert(0, linux_ops_path)
from ssh_config_parser import get_host_config, list_hosts

CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
BLACKLIST_FILE = os.path.join(CONFIG_DIR, 'blacklist.json')


class ConfigManager:
    def __init__(self):
        self._load_blacklist()

    def _load_blacklist(self):
        """Load Docker command blacklist patterns."""
        if os.path.exists(BLACKLIST_FILE):
            with open(BLACKLIST_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.blacklist = data.get("blacklist", [])
                self.confirm_patterns = data.get("confirm_patterns", [])
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

    def _save_blacklist(self):
        """Save blacklist to file."""
        with open(BLACKLIST_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                "blacklist": self.blacklist,
                "confirm_patterns": self.confirm_patterns
            }, f, indent=4)

    def get_server(self, alias):
        """
        Get server configuration from SSH config.

        Args:
            alias: Host alias from SSH config file

        Returns:
            dict: {hostname, user, port, identityfile} or None if not found
        """
        return get_host_config(alias)

    def list_servers(self):
        """
        List all host aliases from SSH config.

        Returns:
            list: List of host aliases
        """
        return list_hosts()

    def check_command(self, command):
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