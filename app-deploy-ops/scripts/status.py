#!/usr/bin/env python
"""状态查看命令 - 代理到 deploy.py status"""

import subprocess
import sys


def main():
    """查看环境状态"""
    if len(sys.argv) < 3:
        print("用法: python scripts/status.py <server> <env>")
        print("示例: python scripts/status.py my-server prod")
        sys.exit(1)

    server = sys.argv[1]
    env = sys.argv[2]

    cmd = [
        sys.executable,
        "-m", "scripts.deploy",
        "status",
        "--server", server,
        "--env", env,
    ]

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()