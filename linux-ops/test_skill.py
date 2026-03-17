import sys
import os
import json

# Add scripts to path
sys.path.append(os.path.join(os.path.dirname(__file__), "scripts"))
from config_manager import ConfigManager

def test_config():
    print("Testing ConfigManager...")
    cm = ConfigManager()
    
    # Test add server
    cm.add_server("test-server", "192.168.1.100", 22, "admin", "secret123")
    print("Server added.")
    
    # Test get server (decrypted)
    server = cm.get_server("test-server")
    assert server["password"] == "secret123", "Password decryption failed"
    print("Password decryption verified.")
    
    # Test list servers
    servers = cm.list_servers()
    assert "test-server" in servers, "List servers failed"
    print("List servers verified.")
    
    # Test blacklist
    allowed, req_conf, reason = cm.check_command("rm -rf /")
    assert not allowed, "Blacklist failed (rm -rf / should be blocked)"
    print("Blacklist (rm -rf /) verified.")
    
    allowed, req_conf, reason = cm.check_command("reboot")
    assert allowed and req_conf, "Confirmation check failed (reboot should require confirm)"
    print("Confirmation check (reboot) verified.")
    
    allowed, req_conf, reason = cm.check_command("ls -la")
    assert allowed and not req_conf, "Normal command check failed"
    print("Normal command check verified.")

    # Clean up
    cm.remove_server("test-server")
    print("Server removed.")

if __name__ == "__main__":
    test_config()
