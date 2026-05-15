#!/usr/bin/env python
"""回滚命令 - 代理到 deploy.py rollback"""

import subprocess
import sys


def main():
    """回滚到指定版本"""
    if len(sys.argv) < 3:
        print("用法: python scripts/rollback.py <server> <env> --version <version>")
        print("示例: python scripts/rollback.py my-server prod --version 2024-01-15_10-30-00")
        sys.exit(1)

    server = sys.argv[1]
    env = sys.argv[2]
    version = None
    preset = "spring-boot-vue"

    i = 3
    while i < len(sys.argv):
        if sys.argv[i] == "--version" and i + 1 < len(sys.argv):
            version = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--preset" and i + 1 < len(sys.argv):
            preset = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    if not version:
        print("错误: 请指定 --version")
        sys.exit(1)

    cmd = [
        sys.executable,
        "-m", "scripts.deploy",
        "rollback",
        "--server", server,
        "--env", env,
        "--preset", preset,
        "--version", version,
    ]

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()