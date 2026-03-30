"""
Test Suite for Docker Ops Skill
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
from docker_commands import DockerCommands


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


def test_docker_commands():
    """Test DockerCommands class generates correct commands."""
    print("\n[Docker Commands Tests]")
    runner = TestRunner()
    dc = DockerCommands()

    # Container commands
    runner.assert_true("docker ps" in dc.ps(), "ps generates docker ps")
    runner.assert_true("docker ps -a" in dc.ps(all=True), "ps -a includes -a flag")
    runner.assert_true("docker logs" in dc.logs("mycontainer"), "logs generates docker logs")
    runner.assert_true("--tail" in dc.logs("mycontainer", lines=50), "logs includes --tail")
    runner.assert_true("docker start" in dc.start("mycontainer"), "start generates docker start")
    runner.assert_true("docker stop" in dc.stop("mycontainer"), "stop generates docker stop")
    runner.assert_true("docker rm" in dc.rm("mycontainer"), "rm generates docker rm")
    runner.assert_true("-f" in dc.rm("mycontainer", force=True), "rm -f includes force flag")
    runner.assert_true("docker exec" in dc.exec_cmd("mycontainer", "ls"), "exec generates docker exec")
    runner.assert_true("docker stats" in dc.stats(), "stats generates docker stats")
    runner.assert_true("docker inspect" in dc.inspect("mycontainer"), "inspect generates docker inspect")

    # Image commands
    runner.assert_true("docker images" in dc.images(), "images generates docker images")
    runner.assert_true("docker pull" in dc.pull("nginx"), "pull generates docker pull")
    runner.assert_true("registry.example.com" in dc.pull("nginx", registry="registry.example.com"), "pull includes registry")
    runner.assert_true("docker push" in dc.push("nginx"), "push generates docker push")
    runner.assert_true("docker rmi" in dc.rmi("nginx"), "rmi generates docker rmi")
    runner.assert_true("docker tag" in dc.tag("src", "dest"), "tag generates docker tag")
    runner.assert_true("docker build" in dc.build("myimage", "."), "build generates docker build")
    runner.assert_true("docker login" in dc.login(), "login generates docker login")
    runner.assert_true("docker logout" in dc.logout(), "logout generates docker logout")

    # Compose commands
    runner.assert_true("docker compose ps" in dc.compose_ps(), "compose_ps generates docker compose ps")
    runner.assert_true("-f compose.yaml" in dc.compose_ps(file="compose.yaml"), "compose_ps includes file")
    runner.assert_true("docker compose up" in dc.compose_up(), "compose_up generates docker compose up")
    runner.assert_true("-d" in dc.compose_up(detach=True), "compose_up includes -d")
    runner.assert_true("docker compose down" in dc.compose_down(), "compose_down generates docker compose down")
    runner.assert_true("-v" in dc.compose_down(volumes=True), "compose_down includes volumes flag")
    runner.assert_true("docker compose logs" in dc.compose_logs(), "compose_logs generates docker compose logs")
    runner.assert_true("docker compose pull" in dc.compose_pull(), "compose_pull generates docker compose pull")
    runner.assert_true("docker compose restart" in dc.compose_restart(), "compose_restart generates docker compose restart")
    runner.assert_true("docker compose build" in dc.compose_build(), "compose_build generates docker compose build")

    # Network commands
    runner.assert_true("docker network ls" in dc.network_ls(), "network_ls generates docker network ls")
    runner.assert_true("docker network create" in dc.network_create("mynetwork"), "network_create generates docker network create")
    runner.assert_true("docker network rm" in dc.network_rm("mynetwork"), "network_rm generates docker network rm")

    # Volume commands
    runner.assert_true("docker volume ls" in dc.volume_ls(), "volume_ls generates docker volume ls")
    runner.assert_true("docker volume create" in dc.volume_create("myvolume"), "volume_create generates docker volume create")
    runner.assert_true("docker volume rm" in dc.volume_rm("myvolume"), "volume_rm generates docker volume rm")

    # System commands
    runner.assert_true("docker info" in dc.info(), "info generates docker info")
    runner.assert_true("docker version" in dc.version(), "version generates docker version")
    runner.assert_true("docker system df" in dc.df(), "df generates docker system df")

    return runner.passed, runner.failed


def test_command_safety():
    """Test Docker command blacklist and confirmation mechanism."""
    print("\n[Docker Command Safety Tests]")
    runner = TestRunner()
    cm = ConfigManager()

    # Blacklisted commands
    tests_blocked = [
        ("docker system prune -af", "docker system prune -af blocked"),
    ]

    for cmd, msg in tests_blocked:
        allowed, _, _ = cm.check_command(cmd)
        runner.assert_true(not allowed, msg)

    # Commands requiring confirmation
    tests_confirm = [
        ("docker stop mycontainer", "docker stop requires confirm"),
        ("docker restart mycontainer", "docker restart requires confirm"),
        ("docker rm mycontainer", "docker rm requires confirm"),
        ("docker rmi myimage", "docker rmi requires confirm"),
        ("docker push myimage", "docker push requires confirm"),
        ("docker build -t myimage .", "docker build requires confirm"),
        ("docker compose up", "docker compose up requires confirm"),
        ("docker compose down", "docker compose down requires confirm"),
        ("docker compose restart", "docker compose restart requires confirm"),
        ("docker compose build", "docker compose build requires confirm"),
    ]

    for cmd, msg in tests_confirm:
        allowed, req_conf, _ = cm.check_command(cmd)
        runner.assert_true(allowed and req_conf, msg)

    # Safe commands - allowed without confirmation
    tests_safe = [
        ("docker ps", "docker ps allowed"),
        ("docker logs mycontainer", "docker logs allowed"),
        ("docker images", "docker images allowed"),
        ("docker pull nginx", "docker pull allowed"),
        ("docker stats", "docker stats allowed"),
        ("docker inspect mycontainer", "docker inspect allowed"),
        ("docker exec mycontainer ls", "docker exec allowed"),
        ("docker compose ps", "docker compose ps allowed"),
        ("docker compose logs", "docker compose logs allowed"),
        ("docker compose pull", "docker compose pull allowed"),
        ("docker network ls", "docker network ls allowed"),
        ("docker volume ls", "docker volume ls allowed"),
        ("docker info", "docker info allowed"),
    ]

    for cmd, msg in tests_safe:
        allowed, req_conf, _ = cm.check_command(cmd)
        runner.assert_true(allowed and not req_conf, msg)

    return runner.passed, runner.failed


def test_ssh_config_integration():
    """Test SSH config integration via linux-ops."""
    print("\n[SSH Config Integration Tests]")
    runner = TestRunner()
    cm = ConfigManager()

    # Test list_servers (should use linux-ops ssh_config_parser)
    servers = cm.list_servers()
    runner.assert_true(isinstance(servers, list), "list_servers returns list")

    # Test get_server
    if servers:
        first_server = servers[0]
        server = cm.get_server(first_server)
        runner.assert_true(server is not None, f"get_server returns config for '{first_server}'")
        if server:
            runner.assert_true("hostname" in server, "Server config contains hostname")

    # Test non-existent server
    server = cm.get_server("__nonexistent__")
    runner.assert_true(server is None, "get_server returns None for non-existent alias")

    return runner.passed, runner.failed


def test_cli_interface():
    """Test CLI command parsing."""
    print("\n[CLI Interface Tests]")
    runner = TestRunner()

    script_path = os.path.join(os.path.dirname(__file__), "scripts", "docker_manager.py")

    # Test help
    result = subprocess.run(
        [sys.executable, script_path, "--help"],
        capture_output=True, text=True, encoding='utf-8'
    )
    runner.assert_true(result.returncode == 0, "Help command succeeds")

    # Test with invalid alias (should fail)
    result = subprocess.run(
        [sys.executable, script_path, "__nonexistent__", "ps"],
        capture_output=True, text=True, encoding='utf-8'
    )
    runner.assert_true(result.returncode == 1, "Invalid alias returns error")

    # Test with valid alias but no action
    result = subprocess.run(
        [sys.executable, script_path, "test-alias"],
        capture_output=True, text=True, encoding='utf-8'
    )
    runner.assert_true(result.returncode == 1, "No action returns error")

    return runner.passed, runner.failed


def main():
    print("=" * 50)
    print("Docker Ops Skill Test Suite")
    print("=" * 50)

    total_passed = 0
    total_failed = 0

    tests = [
        test_docker_commands,
        test_command_safety,
        test_ssh_config_integration,
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