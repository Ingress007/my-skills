"""
Integration test for linux-ops server management functionality.
Tests against a real WSL Ubuntu server.
"""
import sys
import os
import json
import time

# Force UTF-8 on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Setup paths
_scripts_path = os.path.join(os.path.dirname(__file__), "scripts")
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_shared_path = os.path.join(_project_root, "shared")
sys.path.insert(0, _scripts_path)
sys.path.insert(0, _shared_path)

from ssh_client import SSHClient, create_ssh_client
from ssh_config_parser import list_hosts, host_exists, remove_host, get_host_config
from ssh_key_manager import ensure_key_exists, get_default_key_path
from config_manager import ConfigManager
from server_manager import ServerManager
from ssh_manager import SSHManager
from type_defs import ServerAddConfig

# Test server configuration
TEST_SERVER_NAME = "wsl-ubuntu-test"
TEST_SERVER_IP = "172.17.158.79"
TEST_SERVER_USER = "root"
TEST_SERVER_PASSWORD = "fds94014"
TEST_SERVER_PORT = 22


class IntegrationTest:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.steps = []

    def check(self, condition: bool, message: str):
        if condition:
            print(f"  ✓ {message}")
            self.passed += 1
        else:
            print(f"  ✗ {message}")
            self.failed += 1
        self.steps.append((condition, message))
        return condition

    def summary(self):
        print(f"\n  -> 当前: {self.passed} 通过, {self.failed} 失败")


def test_ssh_key_setup():
    """Test 1: SSH key generation / discovery"""
    print("\n" + "=" * 60)
    print("测试 1: SSH Key 设置")
    print("=" * 60)
    runner = IntegrationTest()

    key_path = get_default_key_path()
    print(f"  默认 Key 路径: {key_path}")
    print(f"  Key 是否存在: {os.path.exists(key_path)}")

    success, msg, pub_key = ensure_key_exists()
    runner.check(success, f"SSH Key 确保就绪: {msg}")
    runner.check(pub_key is not None and len(pub_key) > 0, "公钥内容有效")

    runner.summary()
    return runner.passed, runner.failed, pub_key


def test_server_fingerprint(client: SSHClient):
    """Test 2: Get server fingerprint"""
    print("\n" + "=" * 60)
    print("测试 2: 获取服务器指纹")
    print("=" * 60)
    runner = IntegrationTest()

    server_config: ServerAddConfig = {
        "name": TEST_SERVER_NAME,
        "ip": TEST_SERVER_IP,
        "port": TEST_SERVER_PORT,
        "user": TEST_SERVER_USER,
        "password": TEST_SERVER_PASSWORD
    }

    fp_result = client.get_server_fingerprint(server_config)
    runner.check(fp_result["status"] == "success", f"获取指纹成功")
    
    if fp_result["status"] == "success":
        print(f"  指纹: {fp_result['stdout']}")
        runner.check("data" in fp_result, "指纹包含 data 字段")
        if "data" in fp_result:
            fp_data = fp_result["data"]
            runner.check("host_key" in fp_data, "指纹包含 host_key 对象")
            runner.check("key_type" in fp_data, f"密钥类型: {fp_data.get('key_type')}")
            runner.check("fingerprint" in fp_data, f"SHA256 指纹: {fp_data.get('fingerprint')}")
        verified_host_key = fp_data.get("host_key") if fp_result["status"] == "success" and "data" in fp_result else None
    else:
        print(f"  指纹获取失败: {fp_result.get('message')}")
        verified_host_key = None

    runner.summary()
    return runner.passed, runner.failed, verified_host_key


def test_password_connection(client: SSHClient, verified_host_key):
    """Test 3: Password-based connection test"""
    print("\n" + "=" * 60)
    print("测试 3: 密码连接测试")
    print("=" * 60)
    runner = IntegrationTest()

    server_config: ServerAddConfig = {
        "name": TEST_SERVER_NAME,
        "ip": TEST_SERVER_IP,
        "port": TEST_SERVER_PORT,
        "user": TEST_SERVER_USER,
        "password": TEST_SERVER_PASSWORD
    }

    conn_result = client.connect_with_password(server_config, verified_host_key)
    runner.check(conn_result["status"] == "success", f"密码连接成功: {conn_result.get('stdout', '').strip()}")
    if conn_result["status"] != "success":
        print(f"  连接失败: {conn_result.get('message', 'unknown error')}")

    runner.summary()
    return runner.passed, runner.failed


def test_upload_ssh_key(client: SSHClient, verified_host_key, public_key: str):
    """Test 4: Upload SSH public key to server"""
    print("\n" + "=" * 60)
    print("测试 4: 上传 SSH 公钥")
    print("=" * 60)
    runner = IntegrationTest()

    server_config: ServerAddConfig = {
        "name": TEST_SERVER_NAME,
        "ip": TEST_SERVER_IP,
        "port": TEST_SERVER_PORT,
        "user": TEST_SERVER_USER,
        "password": TEST_SERVER_PASSWORD
    }

    upload_result = client.upload_ssh_key(server_config, public_key, verified_host_key)
    runner.check(upload_result["status"] == "success", f"公钥上传: {upload_result.get('stdout', '')}")
    if upload_result["status"] != "success":
        print(f"  上传失败: {upload_result.get('message', 'unknown error')}")

    runner.summary()
    return runner.passed, runner.failed


def test_key_auth(client: SSHClient):
    """Test 5: Verify key-based authentication works"""
    print("\n" + "=" * 60)
    print("测试 5: Key 认证验证")
    print("=" * 60)
    runner = IntegrationTest()

    # Use ensure_key_exists to get the actual key path (handles id_rsa fallback)
    key_success, key_msg, _ = ensure_key_exists()
    if not key_success:
        runner.check(False, f"SSH Key 有问题: {key_msg}")
        runner.summary()
        return runner.passed, runner.failed
    # Extract the actual key path used (may be id_rsa if id_ed25519 doesn't exist)
    actual_key_path = key_msg.split("Key exists at ")[-1] if "Key exists at " in key_msg else get_default_key_path()
    print(f"  实际 Key 路径: {actual_key_path}")

    server = {
        "hostname": TEST_SERVER_IP,
        "user": TEST_SERVER_USER,
        "port": TEST_SERVER_PORT,
        "identityfile": actual_key_path
    }

    auth_result = client.test_key_auth(server)
    runner.check(auth_result["status"] == "success", f"Key 认证: {auth_result.get('stdout', '').strip()}")
    runner.check(auth_result["exit_code"] == 0, "退出码为 0")
    
    if auth_result["status"] != "success":
        print(f"  认证失败: {auth_result.get('message', 'unknown error')}")

    runner.summary()
    return runner.passed, runner.failed


def test_server_manager_api():
    """Test 6: ServerManager API - add, list, remove"""
    print("\n" + "=" * 60)
    print("测试 6: ServerManager API")
    print("=" * 60)
    runner = IntegrationTest()
    
    manager = ServerManager()
    
    # --- Clean up any previous test server ---
    if host_exists(TEST_SERVER_NAME):
        print("  清理上一次测试残留...")
        remove_host(TEST_SERVER_NAME)

    # --- Add server via ServerManager API ---
    print(f"\n  添加服务器: {TEST_SERVER_NAME} ({TEST_SERVER_IP})")
    add_result = manager.add_server(
        name=TEST_SERVER_NAME,
        ip=TEST_SERVER_IP,
        password=TEST_SERVER_PASSWORD,
        port=TEST_SERVER_PORT,
        user=TEST_SERVER_USER,
        verified_host_key=None  # Auto-add for testing
    )
    runner.check(add_result["status"] == "success", f"添加服务器: {add_result.get('message', '')}")
    runner.check(add_result["host_name"] == TEST_SERVER_NAME, f"主机名: {add_result['host_name']}")
    runner.check(len(add_result["steps"]) > 0, "包含步骤详情")
    
    for step in add_result["steps"]:
        runner.check(step["status"] in ("success", "warning"), f"步骤 '{step['step']}': {step['status']}")

    if add_result["status"] != "success":
        print(f"  添加失败: {add_result.get('message', '')}")
        # Still continue to test other features if the server was already set up

    # --- Verify SSH config entry ---
    print(f"\n  验证 SSH config 条目...")
    _, key_msg, pub_key = ensure_key_exists()
    runner.check(host_exists(TEST_SERVER_NAME), f"SSH config 中存在 '{TEST_SERVER_NAME}'")
    
    host_config = get_host_config(TEST_SERVER_NAME)
    if host_config:
        print(f"  配置: {json.dumps(host_config, indent=4, ensure_ascii=False)}")
        runner.check(host_config.get("hostname") == TEST_SERVER_IP, f"Hostname: {host_config.get('hostname')}")
        runner.check(host_config.get("user") == TEST_SERVER_USER, f"User: {host_config.get('user')}")
    else:
        runner.check(False, "获取主机配置")

    runner.summary()
    return runner.passed, runner.failed


def test_ssh_manager_exec():
    """Test 7: SSHManager command execution"""
    print("\n" + "=" * 60)
    print("测试 7: SSHManager 命令执行")
    print("=" * 60)
    runner = IntegrationTest()
    
    manager = SSHManager()

    # --- Execute safe commands ---
    print("\n  --- 安全命令测试 ---")
    
    # uptime
    result = manager.execute(TEST_SERVER_NAME, "uptime")
    runner.check(result["status"] == "success", f"uptime: 成功")
    runner.check(result["exit_code"] == 0, f"uptime exit_code=0")
    if result["status"] == "success":
        print(f"    stdout: {result['stdout'].strip()[:100]}")

    # uname -a
    result = manager.execute(TEST_SERVER_NAME, "uname -a")
    runner.check(result["status"] == "success", f"uname -a: 成功")
    if result["status"] == "success":
        print(f"    stdout: {result['stdout'].strip()[:120]}")

    # df -h
    result = manager.execute(TEST_SERVER_NAME, "df -h /")
    runner.check(result["status"] == "success", f"df -h: 成功")
    if result["status"] == "success":
        lines = result['stdout'].strip().split('\n')
        print(f"    {lines[0]}")
        print(f"    {lines[1]}")

    # free -m
    result = manager.execute(TEST_SERVER_NAME, "free -m")
    runner.check(result["status"] == "success", f"free -m: 成功")
    if result["status"] == "success":
        mem_line = result['stdout'].strip().split('\n')[1]
        print(f"    {mem_line}")

    # ls
    result = manager.execute(TEST_SERVER_NAME, "ls /root")
    runner.check(result["status"] == "success", f"ls /root: 成功")
    runner.check(result["exit_code"] == 0, "ls exit_code=0")

    # whoami
    result = manager.execute(TEST_SERVER_NAME, "whoami")
    runner.check(result["status"] == "success", f"whoami: 成功")
    if result["status"] == "success":
        runner.check(result["stdout"].strip() == "root", f"当前用户是 {result['stdout'].strip()}")

    runner.summary()
    return runner.passed, runner.failed


def test_command_safety_integration():
    """Test 8: Command safety integration"""
    print("\n" + "=" * 60)
    print("测试 8: 命令安全机制")
    print("=" * 60)
    runner = IntegrationTest()

    manager = SSHManager()
    cm = ConfigManager()

    # --- Blacklisted commands should be blocked ---
    print("\n  --- 黑名单命令测试 ---")
    blacklist_tests = [
        ("rm -rf /", "rm -rf /"),
        ("mkfs.ext4 /dev/sda1", "mkfs"),
        ("dd if=/dev/zero of=/dev/sda", "dd"),
    ]
    for cmd, desc in blacklist_tests:
        result = manager.execute(TEST_SERVER_NAME, cmd)
        runner.check(
            result["status"] == "error" and "blocked" in result.get("message", "").lower(),
            f"黑名单拦截 [{desc}]: {result.get('message', '')[:60]}"
        )
        runner.check(result["exit_code"] == -1, f"exit_code = -1")

    # --- Commands requiring --confirm ---
    print("\n  --- 确认命令测试 (无 --confirm) ---")
    confirm_tests = [
        ("reboot", "reboot"),
        ("systemctl restart sshd", "systemctl restart"),
        ("rm /tmp/test.txt", "rm file"),
    ]
    for cmd, desc in confirm_tests:
        result = manager.execute(TEST_SERVER_NAME, cmd)
        runner.check(
            result["status"] == "error" and "confirmation" in result.get("message", "").lower(),
            f"确认拦截 [{desc}]: {result.get('message', '')[:60]}"
        )
        runner.check(result["exit_code"] == -1, f"exit_code = -1")

    # --- Commands with --confirm should pass through ---
    print("\n  --- 确认命令测试 (带 --confirm) ---")
    allowed, req_conf, reason = cm.check_command("systemctl status sshd")
    runner.check(allowed and not req_conf, f"systemctl status 安全: {reason}")

    # Test non-existent server
    result = manager.execute("__nonexistent__", "ls")
    runner.check(
        result["status"] == "error" and "not found" in result.get("message", "").lower(),
        f"不存在的服务器: {result.get('message', '')[:60]}"
    )

    runner.summary()
    return runner.passed, runner.failed


def test_diagnose():
    """Test 9: System diagnosis"""
    print("\n" + "=" * 60)
    print("测试 9: 系统诊断")
    print("=" * 60)
    runner = IntegrationTest()

    manager = SSHManager()
    diagnose_script = os.path.join(os.path.dirname(__file__), "scripts", "diagnose.sh")

    if not os.path.exists(diagnose_script):
        print("  ⚠  diagnose.sh 不存在，跳过诊断测试")
        runner.check(False, "diagnose.sh 文件存在")
        runner.summary()
        return runner.passed, runner.failed

    print(f"  诊断脚本: {diagnose_script}")
    result = manager.execute_script(TEST_SERVER_NAME, diagnose_script)
    runner.check(result["status"] == "success", f"系统诊断执行成功: exit_code={result['exit_code']}")

    if result["status"] == "success":
        stdout = result.get("stdout", "")
        print(f"  诊断输出 ({len(stdout)} bytes):")
        for line in stdout.strip().split('\n')[:25]:
            print(f"    | {line}")
        if stdout.count('\n') > 25:
            print(f"    | ... (共 {stdout.count('\n')} 行)")
        
        # Verify key information is present
        runner.check("Memory:" in stdout or "Mem:" in stdout or "mem" in stdout.lower(), "诊断包含内存信息")
        runner.check("CPU" in stdout or "cpu" in stdout.lower(), "诊断包含 CPU 信息")
        runner.check("Disk" in stdout or "disk" in stdout.lower() or "dev" in stdout, "诊断包含磁盘信息")
    else:
        print(f"  诊断失败: {result.get('message', '')}")

    runner.summary()
    return runner.passed, runner.failed


def test_list_servers():
    """Test 10: List servers"""
    print("\n" + "=" * 60)
    print("测试 10: 列出服务器")
    print("=" * 60)
    runner = IntegrationTest()

    manager = ServerManager()
    result = manager.list_servers()
    
    runner.check(result["status"] == "success", "list_servers 返回成功")
    runner.check("hosts" in result, "包含 hosts 字段")
    runner.check("count" in result, "包含 count 字段")
    runner.check(isinstance(result["hosts"], list), "hosts 是列表")
    runner.check(result["count"] >= 1, f"至少有一个主机: {result['count']}")
    runner.check(TEST_SERVER_NAME in result["hosts"], f"测试主机 '{TEST_SERVER_NAME}' 在列表中")

    print(f"  配置路径: {result['config_path']}")
    print(f"  主机数: {result['count']}")
    print(f"  主机列表: {result['hosts']}")

    runner.summary()
    return runner.passed, runner.failed


def test_remove_server():
    """Test 11: Remove server (cleanup)"""
    print("\n" + "=" * 60)
    print("测试 11: 删除服务器")
    print("=" * 60)
    runner = IntegrationTest()

    # Skip if host was not added
    if not host_exists(TEST_SERVER_NAME):
        print("  ⚠  主机不存在，跳过删除测试")
        runner.check(True, "主机已不存在")
        runner.summary()
        return runner.passed, runner.failed

    manager = ServerManager()
    result = manager.remove_server(TEST_SERVER_NAME)
    runner.check(result["status"] == "success", f"删除服务器: {result.get('message', '')}")

    # Verify it's gone
    runner.check(not host_exists(TEST_SERVER_NAME), "SSH config 中已删除")
    
    # List should no longer include it
    list_result = manager.list_servers()
    runner.check(TEST_SERVER_NAME not in list_result["hosts"], "list 中已不包含")
    
    # Re-add for subsequent tests (only if we successfully removed)
    if result["status"] == "success":
        # Re-add the server for the user to keep
        add_result = manager.add_server(
            name=TEST_SERVER_NAME,
            ip=TEST_SERVER_IP,
            password=TEST_SERVER_PASSWORD,
            port=TEST_SERVER_PORT,
            user=TEST_SERVER_USER,
            verified_host_key=None
        )
        if add_result["status"] == "success":
            print(f"  已重新添加 {TEST_SERVER_NAME}")
        else:
            print(f"  重新添加失败: {add_result.get('message', '')}")

    runner.summary()
    return runner.passed, runner.failed


def main():
    print("=" * 60)
    print("  Linux Ops - 服务器管理功能集成测试")
    print("  Target: wsl-ubuntu-test (172.17.158.79)")
    print("=" * 60)

    total_passed = 0
    total_failed = 0
    public_key = ""

    tests = []

    # Phase 1: SSH Key Setup
    p, f, public_key = test_ssh_key_setup()
    total_passed += p
    total_failed += f

    if public_key:
        pub_key_trunc = public_key[:80] + "..." if len(public_key) > 80 else public_key
        print(f"\n  公钥: {pub_key_trunc}")

    # Phase 2: Direct SSH connection tests
    client = create_ssh_client(timeout=15)

    p, f, verified_host_key = test_server_fingerprint(client)
    total_passed += p
    total_failed += f

    p, f = test_password_connection(client, verified_host_key)
    total_passed += p
    total_failed += f

    if public_key:
        p, f = test_upload_ssh_key(client, verified_host_key, public_key)
        total_passed += p
        total_failed += f

        p, f = test_key_auth(client)
        total_passed += p
        total_failed += f

    # Phase 3: ServerManager integration test
    p, f = test_server_manager_api()
    total_passed += p
    total_failed += f

    # Phase 4: SSHManager command execution
    p, f = test_ssh_manager_exec()
    total_passed += p
    total_failed += f

    # Phase 5: Command safety
    p, f = test_command_safety_integration()
    total_passed += p
    total_failed += f

    # Phase 6: Diagnostics
    p, f = test_diagnose()
    total_passed += p
    total_failed += f

    # Phase 7: List servers
    p, f = test_list_servers()
    total_passed += p
    total_failed += f

    # Phase 8: Cleanup test (remove then re-add)
    p, f = test_remove_server()
    total_passed += p
    total_failed += f

    print("\n" + "=" * 60)
    if total_failed == 0:
        print(f"  全部 {total_passed} 项测试通过 ✓")
    else:
        print(f"  结果: {total_passed} 通过, {total_failed} 失败 ✗")
    print("=" * 60)

    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())