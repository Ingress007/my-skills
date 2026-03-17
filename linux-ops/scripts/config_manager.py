import json
import os
import re
from cryptography.fernet import Fernet

CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
KEY_FILE = os.path.join(CONFIG_DIR, 'secret.key')
SERVERS_FILE = os.path.join(CONFIG_DIR, 'servers.json')
BLACKLIST_FILE = os.path.join(CONFIG_DIR, 'blacklist.json')

class ConfigManager:
    def __init__(self):
        self._load_key()
        self._load_servers()
        self._load_blacklist()

    def _load_key(self):
        if not os.path.exists(KEY_FILE):
            self.key = Fernet.generate_key()
            with open(KEY_FILE, 'wb') as f:
                f.write(self.key)
        else:
            with open(KEY_FILE, 'rb') as f:
                self.key = f.read()
        self.cipher = Fernet(self.key)

    def _encrypt(self, text):
        if not text: return ""
        return self.cipher.encrypt(text.encode()).decode()

    def _decrypt(self, text):
        if not text: return ""
        return self.cipher.decrypt(text.encode()).decode()

    def _load_servers(self):
        if os.path.exists(SERVERS_FILE):
            try:
                with open(SERVERS_FILE, 'r', encoding='utf-8') as f:
                    self.servers = json.load(f)
            except:
                self.servers = {}
        else:
            self.servers = {}

    def save_servers(self):
        with open(SERVERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.servers, f, indent=4, ensure_ascii=False)

    def add_server(self, alias, hostname, port, username, password=None, key_path=None):
        self.servers[alias] = {
            "hostname": hostname,
            "port": port,
            "username": username,
            "password": self._encrypt(password) if password else None,
            "key_path": key_path
        }
        self.save_servers()

    def remove_server(self, alias):
        if alias in self.servers:
            del self.servers[alias]
            self.save_servers()
            return True
        return False

    def get_server(self, alias):
        server = self.servers.get(alias)
        if server and server.get("password"):
            # Return a copy with decrypted password
            s = server.copy()
            s["password"] = self._decrypt(server["password"])
            return s
        return server

    def list_servers(self):
        return list(self.servers.keys())

    def _load_blacklist(self):
        if os.path.exists(BLACKLIST_FILE):
            with open(BLACKLIST_FILE, 'r') as f:
                data = json.load(f)
                self.blacklist = data.get("blacklist", [])
                self.confirm_patterns = data.get("confirm_patterns", [])
        else:
            # Defaults
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
        with open(BLACKLIST_FILE, 'w') as f:
            json.dump({
                "blacklist": self.blacklist,
                "confirm_patterns": self.confirm_patterns
            }, f, indent=4)

    def check_command(self, command):
        """
        Returns (allowed, requires_confirmation, reason)
        """
        for pattern in self.blacklist:
            if re.search(pattern, command):
                return False, False, f"Command matches blacklist pattern: {pattern}"
        
        for pattern in self.confirm_patterns:
            if re.search(pattern, command):
                return True, True, f"Command matches confirmation pattern: {pattern}"
                
        return True, False, "OK"
