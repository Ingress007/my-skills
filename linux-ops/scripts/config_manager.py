"""
Config Manager - Manage command safety blacklist and SSH config integration
"""
import json
import os
import re
import sys

# Add current dir to path to import ssh_config_parser
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from ssh_config_parser import get_host_config, list_hosts

CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
BLACKLIST_FILE = os.path.join(CONFIG_DIR, 'blacklist.json')


class ConfigManager:
    def __init__(self):
        self._load_blacklist()

    def _load_blacklist(self):
        """Load command blacklist patterns."""
        if os.path.exists(BLACKLIST_FILE):
            with open(BLACKLIST_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.blacklist = data.get("blacklist", [])
                self.confirm_patterns = data.get("confirm_patterns", [])
        else:
            # Default safety patterns
            self.blacklist = [
                r"^rm\s+-rf\s+/$",
                r"^mkfs",
                r"^dd\s+if="
            ]
            self.confirm_patterns = [
                r"^rm",
                r"^reboot",
                r"^shutdown",
                r"^systemctl\s+(stop|restart)"
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
        Check if a command is allowed and whether it requires confirmation.

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