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


class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.test_alias = "__test_server__"

    def assert_true(self, condition, message):
        if condition:
            print(f"  ✓ {message}")
            self.passed += 1
        else:
            print(f"  ✗ {message}")
            self.failed += 1

    def cleanup(self, cm):
        """Remove test server if exists."""
        if self.test_alias in cm.list_servers():
            cm.remove_server(self.test_alias)


def test_config_manager():
    """Test ConfigManager core functionality."""
    print("\n[ConfigManager Tests]")
    runner = TestRunner()
    cm = ConfigManager()

    runner.cleanup(cm)

    # Test add server
    cm.add_server(runner.test_alias, "192.168.1.100", 22, "admin", password="secret123")
    runner.assert_true(runner.test_alias in cm.list_servers(), "Add server")

    # Test password encryption/decryption
    server = cm.get_server(runner.test_alias)
    runner.assert_true(server["password"] == "secret123", "Password encryption/decryption")

    # Test server info
    runner.assert_true(server["hostname"] == "192.168.1.100", "Server hostname stored")
    runner.assert_true(server["username"] == "admin", "Server username stored")
    runner.assert_true(server["port"] == 22, "Server port stored")

    # Test list servers
    servers = cm.list_servers()
    runner.assert_true(runner.test_alias in servers, "List servers")

    # Test remove server
    cm.remove_server(runner.test_alias)
    runner.assert_true(runner.test_alias not in cm.list_servers(), "Remove server")

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

    runner.cleanup(cm)

    # Test non-existent server
    result = manager.execute("non-existent-server", "ls")
    runner.assert_true(result["status"] == "error", "Non-existent server returns error")
    runner.assert_true("not found" in result["message"], "Error message contains 'not found'")

    # Test blacklisted command
    cm.add_server(runner.test_alias, "192.168.1.100", 22, "admin", password="test")
    result = manager.execute(runner.test_alias, "rm -rf /")
    runner.assert_true(result["status"] == "error", "Blacklisted command returns error")
    runner.assert_true("blocked" in result["message"], "Error message contains 'blocked'")

    # Test command requiring confirmation (without --confirm)
    result = manager.execute(runner.test_alias, "reboot")
    runner.assert_true(result["status"] == "error", "Unconfirmed command returns error")
    runner.assert_true("confirmation" in result["message"], "Error message mentions confirmation")

    # Test command requiring confirmation (with --confirm)
    # Note: We can't test actual execution without a real server,
    # but we can verify the confirmation check passes
    allowed, req_conf, _ = cm.check_command("reboot")
    runner.assert_true(allowed and req_conf, "reboot allowed with confirm flag")

    runner.cleanup(cm)
    return runner.passed, runner.failed


def test_cli_interface():
    """Test CLI command parsing."""
    print("\n[CLI Interface Tests]")
    runner = TestRunner()

    script_path = os.path.join(os.path.dirname(__file__), "scripts", "ssh_manager.py")

    # Test help command
    result = subprocess.run(
        [sys.executable, script_path, "--help"],
        capture_output=True, text=True
    )
    runner.assert_true(result.returncode == 0, "Help command succeeds")

    # Test list-servers command
    result = subprocess.run(
        [sys.executable, script_path, "list-servers"],
        capture_output=True, text=True
    )
    runner.assert_true(result.returncode == 0, "list-servers command succeeds")

    # Test invalid command
    result = subprocess.run(
        [sys.executable, script_path, "exec", "non-existent", "ls"],
        capture_output=True, text=True
    )
    runner.assert_true(result.returncode == 1, "Invalid server returns error code 1")

    return runner.passed, runner.failed


def main():
    print("=" * 50)
    print("Linux Ops Skill Test Suite")
    print("=" * 50)

    total_passed = 0
    total_failed = 0

    tests = [
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