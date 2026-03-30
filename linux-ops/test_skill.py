"""
Test Suite for Linux Ops Skill - SSH Config Based Version
"""
import sys
import os
import json
import subprocess

# Force UTF-8 on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Add scripts to path
scripts_path = os.path.join(os.path.dirname(__file__), "scripts")
sys.path.insert(0, scripts_path)
from config_manager import ConfigManager
from ssh_manager import SSHManager
from ssh_config_parser import parse_ssh_config, list_hosts, get_host_config


class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0

    def assert_true(self, condition, message):
        if condition:
            print(f"  ✓ {message}")
            self.passed += 1
        else:
            print(f"  ✗ {message}")
            self.failed += 1


def test_ssh_config_parser():
    """Test SSH config file parsing."""
    print("\n[SSH Config Parser Tests]")
    runner = TestRunner()

    hosts = parse_ssh_config()
    runner.assert_true(isinstance(hosts, dict), "parse_ssh_config returns dict")

    host_list = list_hosts()
    runner.assert_true(isinstance(host_list, list), "list_hosts returns list")

    if host_list:
        first_host = host_list[0]
        config = get_host_config(first_host)
        runner.assert_true(config is not None, f"get_host_config returns config for '{first_host}'")
        if config:
            runner.assert_true("hostname" in config, "Config contains hostname")
            runner.assert_true("port" in config, "Config contains port")
            runner.assert_true("user" in config, "Config contains user")

    config = get_host_config("__nonexistent__")
    runner.assert_true(config is None, "get_host_config returns None for non-existent host")

    return runner.passed, runner.failed


def test_config_manager():
    """Test ConfigManager SSH config integration."""
    print("\n[ConfigManager Tests]")
    runner = TestRunner()
    cm = ConfigManager()

    servers = cm.list_servers()
    runner.assert_true(isinstance(servers, list), "list_servers returns list")

    if servers:
        first_server = servers[0]
        server = cm.get_server(first_server)
        runner.assert_true(server is not None, f"get_server returns config for '{first_server}'")
        if server:
            runner.assert_true("hostname" in server, "Server config contains hostname")

    server = cm.get_server("__nonexistent__")
    runner.assert_true(server is None, "get_server returns None for non-existent alias")

    return runner.passed, runner.failed


def test_command_safety():
    """Test command blacklist and confirmation mechanism."""
    print("\n[Command Safety Tests]")
    runner = TestRunner()
    cm = ConfigManager()

    # Blacklisted commands
    tests_blocked = [
        ("rm -rf /", "rm -rf / blocked"),
        ("mkfs.ext4 /dev/sda1", "mkfs blocked"),
        ("dd if=/dev/zero of=/dev/sda", "dd blocked"),
    ]

    for cmd, msg in tests_blocked:
        allowed, _, _ = cm.check_command(cmd)
        runner.assert_true(not allowed, msg)

    # Commands requiring confirmation
    tests_confirm = [
        ("reboot", "reboot requires confirm"),
        ("shutdown -h now", "shutdown requires confirm"),
        ("systemctl restart nginx", "systemctl restart requires confirm"),
        ("systemctl stop mysql", "systemctl stop requires confirm"),
        ("rm /tmp/file", "rm requires confirm"),
    ]

    for cmd, msg in tests_confirm:
        allowed, req_conf, _ = cm.check_command(cmd)
        runner.assert_true(allowed and req_conf, msg)

    # Safe commands
    tests_safe = [
        ("ls -la", "ls allowed"),
        ("uptime", "uptime allowed"),
        ("df -h", "df allowed"),
        ("cat /var/log/syslog", "cat allowed"),
        ("docker ps", "docker ps allowed"),
        ("free -m", "free allowed"),
        ("top -bn1", "top allowed"),
    ]

    for cmd, msg in tests_safe:
        allowed, req_conf, _ = cm.check_command(cmd)
        runner.assert_true(allowed and not req_conf, msg)

    return runner.passed, runner.failed


def test_ssh_manager_mock():
    """Test SSHManager without real SSH connection."""
    print("\n[SSHManager Mock Tests]")
    runner = TestRunner()
    cm = ConfigManager()
    manager = SSHManager()

    # Test non-existent server
    result = manager.execute("__nonexistent__", "ls")
    runner.assert_true(result["status"] == "error", "Non-existent server returns error")
    runner.assert_true("not found" in result["message"].lower(), "Error message mentions 'not found'")

    servers = cm.list_servers()
    if servers:
        test_host = servers[0]

        # Test blacklisted command
        result = manager.execute(test_host, "rm -rf /")
        runner.assert_true(result["status"] == "error", "Blacklisted command returns error")
        runner.assert_true("blocked" in result["message"].lower(), "Error message mentions 'blocked'")

        # Test command requiring confirmation (without --confirm)
        result = manager.execute(test_host, "reboot")
        runner.assert_true(result["status"] == "error", "Unconfirmed command returns error")
        runner.assert_true("confirmation" in result["message"].lower(), "Error message mentions confirmation")

        # Verify confirmation check passes for reboot with confirm=True
        allowed, req_conf, _ = cm.check_command("reboot")
        runner.assert_true(allowed and req_conf, "reboot is allowed with confirmation requirement")

    return runner.passed, runner.failed


def test_cli_interface():
    """Test CLI command parsing."""
    print("\n[CLI Interface Tests]")
    runner = TestRunner()

    script_path = os.path.join(os.path.dirname(__file__), "scripts", "ssh_manager.py")

    # Test help
    result = subprocess.run(
        [sys.executable, script_path, "--help"],
        capture_output=True, text=True, encoding='utf-8'
    )
    runner.assert_true(result.returncode == 0, "Help command succeeds")

    # Test list-servers
    result = subprocess.run(
        [sys.executable, script_path, "list-servers"],
        capture_output=True, text=True, encoding='utf-8'
    )
    runner.assert_true(result.returncode == 0, "list-servers succeeds")

    try:
        output = json.loads(result.stdout)
        runner.assert_true("hosts" in output, "list-servers output contains 'hosts'")
    except json.JSONDecodeError:
        runner.assert_true(False, "list-servers returns valid JSON")

    # Test invalid server
    result = subprocess.run(
        [sys.executable, script_path, "exec", "__nonexistent__", "ls"],
        capture_output=True, text=True, encoding='utf-8'
    )
    runner.assert_true(result.returncode == 1, "Invalid server returns error")

    return runner.passed, runner.failed


def main():
    print("=" * 50)
    print("Linux Ops Skill Test Suite")
    print("=" * 50)

    total_passed = 0
    total_failed = 0

    tests = [
        test_ssh_config_parser,
        test_config_manager,
        test_command_safety,
        test_ssh_manager_mock,
        test_cli_interface,
    ]

    for test in tests:
        try:
            passed, failed = test()
            total_passed += passed
            total_failed += failed
        except Exception as e:
            print(f"  ✗ Test crashed: {e}")
            total_failed += 1

    print("\n" + "=" * 50)
    print(f"Results: {total_passed} passed, {total_failed} failed")
    print("=" * 50)

    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())