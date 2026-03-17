import sys
import os

# Add scripts to path
sys.path.append(os.path.join(os.path.dirname(__file__), "scripts"))
from config_manager import ConfigManager

def add_server():
    print("Adding server safely...")
    cm = ConfigManager()
    
    # Server details
    alias = "我的京东服务器"
    hostname = "117.72.36.206"
    port = 22
    user = "root"
    # Password with special characters that caused shell issues
    password = "mL2,|(kTjK[MG5h"
    
    try:
        cm.add_server(alias, hostname, port, user, password=password)
        print(f"Server '{alias}' added successfully.")
    except Exception as e:
        print(f"Failed to add server: {e}")

if __name__ == "__main__":
    add_server()
