"""
RocketMQ Config - Configuration management for RocketMQ ops
Supports 4-level priority: CLI > Auto-detect > Config file > Default
With Docker auto-detection capabilities.
"""
import subprocess
import json
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

# 注意：UTF-8 包装由调用脚本负责，此处不做包装避免冲突


@dataclass
class RocketMQPaths:
    """RocketMQ path configuration"""
    mqadmin_path: str = "/home/rocketmq/rocketmq-5.3.0/bin/mqadmin"
    namesrv_container: str = "rmqnamesrv"
    broker_container: str = "rmqbroker"
    namesrv_addr: str = "rmqnamesrv:9876"
    cluster_name: str = "DefaultCluster"


@dataclass
class TopicDefaults:
    """Topic default configuration"""
    read_queue: int = 4
    write_queue: int = 4
    perm: int = 6  # RW
    message_type: str = "NORMAL"


@dataclass
class RocketMQConfig:
    """Complete RocketMQ configuration"""
    paths: RocketMQPaths = field(default_factory=RocketMQPaths)
    topics: TopicDefaults = field(default_factory=TopicDefaults)


def get_config_file_path() -> Path:
    """Get configuration file path"""
    script_dir = Path(__file__).resolve().parent
    return script_dir.parent / "config.yaml"


def load_config_from_file(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from YAML file"""
    config_path = path or get_config_file_path()
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    return {}


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dicts"""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def run_ssh_command(server_alias: str, command: str) -> Dict[str, Any]:
    """通过 ssh_manager.py 执行远程命令"""
    script_dir = Path(__file__).resolve()
    project_root = script_dir.parent.parent.parent  # my-skills/
    ssh_manager_path = project_root / 'linux-ops' / 'scripts' / 'ssh_manager.py'

    result = subprocess.run(
        ['python', str(ssh_manager_path), 'exec', server_alias, command],
        capture_output=True,
        text=True
    )

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            'status': 'error',
            'stdout': result.stdout,
            'stderr': result.stderr,
            'exit_code': result.returncode
        }


# ========== Docker Auto-Detection Functions ==========

def detect_rocketmq_containers(server_alias: str) -> Dict[str, str]:
    """
    Auto-detect RocketMQ container names via Docker.

    Detects:
    - namesrv_container: NameServer container
    - broker_container: Broker container

    Args:
        server_alias: SSH server alias

    Returns:
        dict: {namesrv_container, broker_container}
    """
    result = run_ssh_command(server_alias, "docker ps --format '{{.Names}} {{.Image}}'")

    if result.get('exit_code', 0) != 0 or result.get('status') == 'error':
        return {}

    containers: Dict[str, str] = {}
    output = result.get('stdout', '')

    for line in output.strip().split('\n'):
        if not line:
            continue
        parts = line.strip().split()
        if len(parts) >= 2:
            name = parts[0]
            image = parts[1].lower()

            # NameServer detection
            # 容器名包含 namesrv 或镜像包含 rocketmq 且容器名暗示 namesrv
            if 'namesrv' in name.lower():
                containers['namesrv_container'] = name
            elif 'rocketmq' in image and 'namesrv' not in containers:
                # 首个 rocketmq 容器可能是 namesrv（如果有多个）
                pass

            # Broker detection
            # 容器名包含 broker
            if 'broker' in name.lower():
                containers['broker_container'] = name

            # 如果镜像包含 rocketmq，根据容器名推断
            if 'rocketmq' in image:
                if 'namesrv' in name.lower() and 'namesrv_container' not in containers:
                    containers['namesrv_container'] = name
                elif 'broker' in name.lower() and 'broker_container' not in containers:
                    containers['broker_container'] = name
                # rmqnamesrv / rmqbroker 常见命名模式
                elif name.startswith('rmq') and 'namesrv' in name.lower():
                    containers['namesrv_container'] = name
                elif name.startswith('rmq') and 'broker' in name.lower():
                    containers['broker_container'] = name

    return containers


def detect_mqadmin_path(server_alias: str, container: str) -> Optional[str]:
    """
    Auto-detect mqadmin path inside container.

    Args:
        server_alias: SSH server alias
        container: Container name

    Returns:
        str: mqadmin path or None
    """
    # 尝试 find 命令查找
    result = run_ssh_command(
        server_alias,
        f"docker exec {container} find /home /opt /usr -name mqadmin -type f 2>/dev/null | head -1"
    )

    if result.get('exit_code', 0) == 0:
        path = result.get('stdout', '').strip()
        if path and 'mqadmin' in path:
            return path

    # 尝试常见路径
    common_paths = [
        "/home/rocketmq/rocketmq-5.3.0/bin/mqadmin",
        "/home/rocketmq/rocketmq-5.2.0/bin/mqadmin",
        "/home/rocketmq/rocketmq-5.1.0/bin/mqadmin",
        "/opt/rocketmq/bin/mqadmin",
        "/usr/local/rocketmq/bin/mqadmin",
    ]

    for path in common_paths:
        result = run_ssh_command(
            server_alias,
            f"docker exec {container} test -f {path} && echo {path}"
        )
        if result.get('stdout', '').strip():
            return path

    return None


def detect_cluster_name(server_alias: str, namesrv_container: str, mqadmin_path: str) -> Optional[str]:
    """
    Auto-detect RocketMQ cluster name.

    Args:
        server_alias: SSH server alias
        namesrv_container: NameServer container name
        mqadmin_path: mqadmin command path

    Returns:
        str: cluster name or None
    """
    result = run_ssh_command(
        server_alias,
        f"docker exec {namesrv_container} {mqadmin_path} clusterList -n localhost:9876 2>/dev/null"
    )

    stdout = result.get('stdout', '')

    # 解析集群名称，格式通常是表格形式
    # Cluster Name    Broker Name    Broker Addr
    for line in stdout.strip().split('\n'):
        if 'Cluster' in line or 'DefaultCluster' in line:
            parts = line.strip().split()
            if parts:
                cluster = parts[0]
                if cluster and not cluster.startswith('#'):
                    return cluster

    # 默认值
    return "DefaultCluster"


def auto_detect_config(server_alias: str) -> Dict[str, Any]:
    """
    Auto-detect all RocketMQ configuration from Docker environment.

    Args:
        server_alias: SSH server alias

    Returns:
        dict: Detected configuration
    """
    detected: Dict[str, Any] = {}

    # 1. 检测容器名称
    containers = detect_rocketmq_containers(server_alias)
    detected.update(containers)

    # 2. 检测 mqadmin 路径（需要 broker 容器）
    broker = containers.get('broker_container')
    if broker:
        mqadmin_path = detect_mqadmin_path(server_alias, broker)
        if mqadmin_path:
            detected['mqadmin_path'] = mqadmin_path

    # 3. 检测集群名称（需要 namesrv 和 mqadmin）
    namesrv = containers.get('namesrv_container')
    mqadmin = detected.get('mqadmin_path')
    if namesrv and mqadmin:
        cluster = detect_cluster_name(server_alias, namesrv, mqadmin)
        if cluster:
            detected['cluster_name'] = cluster

    # 4. 推导 namesrv_addr
    if namesrv:
        detected['namesrv_addr'] = f"{namesrv}:9876"

    return detected


def get_rocketmq_config(
    cli_overrides: Optional[Dict[str, Any]] = None,
    auto_detect_server: Optional[str] = None
) -> RocketMQConfig:
    """
    Get RocketMQ configuration with 4-level priority.

    Priority: CLI > Auto-detect > Config file > Default

    Args:
        cli_overrides: CLI argument overrides
        auto_detect_server: Server alias for auto-detection

    Returns:
        RocketMQConfig instance
    """
    # 1. Default values (lowest priority)
    default_config: Dict[str, Any] = {
        "rocketmq": {
            "mqadmin_path": "/home/rocketmq/rocketmq-5.3.0/bin/mqadmin",
            "namesrv_container": "rmqnamesrv",
            "broker_container": "rmqbroker",
            "namesrv_addr": "rmqnamesrv:9876",
            "cluster_name": "DefaultCluster",
            "default_read_queue": 4,
            "default_write_queue": 4,
            "default_perm": 6,
            "default_message_type": "NORMAL",
        }
    }

    # 2. Config file
    file_config = load_config_from_file()

    # 3. Auto-detect (if server provided)
    auto_config: Dict[str, Any] = {}
    if auto_detect_server:
        detected = auto_detect_config(auto_detect_server)
        auto_config = {"rocketmq": detected}

    # 4. CLI arguments (highest priority)
    cli_config = {"rocketmq": cli_overrides or {}}

    # Merge all configs (priority: cli > auto > file > default)
    merged = deep_merge(default_config, file_config)
    merged = deep_merge(merged, auto_config)
    merged = deep_merge(merged, cli_config)

    rocketmq_cfg = merged.get("rocketmq", {})

    paths = RocketMQPaths(
        mqadmin_path=rocketmq_cfg.get("mqadmin_path", default_config["rocketmq"]["mqadmin_path"]),
        namesrv_container=rocketmq_cfg.get("namesrv_container", default_config["rocketmq"]["namesrv_container"]),
        broker_container=rocketmq_cfg.get("broker_container", default_config["rocketmq"]["broker_container"]),
        namesrv_addr=rocketmq_cfg.get("namesrv_addr", default_config["rocketmq"]["namesrv_addr"]),
        cluster_name=rocketmq_cfg.get("cluster_name", default_config["rocketmq"]["cluster_name"]),
    )

    topics = TopicDefaults(
        read_queue=rocketmq_cfg.get("default_read_queue", default_config["rocketmq"]["default_read_queue"]),
        write_queue=rocketmq_cfg.get("default_write_queue", default_config["rocketmq"]["default_write_queue"]),
        perm=rocketmq_cfg.get("default_perm", default_config["rocketmq"]["default_perm"]),
        message_type=rocketmq_cfg.get("default_message_type", default_config["rocketmq"]["default_message_type"]),
    )

    return RocketMQConfig(paths=paths, topics=topics)


def get_mqadmin_path(container: str, config: Optional[RocketMQConfig] = None) -> str:
    """
    Get mqadmin command path for docker exec.

    Args:
        container: Container name
        config: Configuration object

    Returns:
        docker exec command prefix + mqadmin path
    """
    cfg = config or get_rocketmq_config()
    return f'docker exec {container} {cfg.paths.mqadmin_path}'


# ========== CLI: Config Detection Tool ==========

def main_detect() -> None:
    """CLI for detecting RocketMQ configuration"""
    import argparse
    import sys
    import io

    # 修复 Windows 终端中文编码问题
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    parser = argparse.ArgumentParser(description='RocketMQ Configuration Detection')
    parser.add_argument('server', help='SSH server alias')
    parser.add_argument('--save', action='store_true', help='Save to config.yaml')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    print(f"Detecting RocketMQ configuration on {args.server}...")
    print()

    detected = auto_detect_config(args.server)

    print("Detected configuration:")
    print("-" * 40)
    for key, value in detected.items():
        print(f"  {key}: {value}")
    print()

    if not detected:
        print("Warning: Could not detect any RocketMQ configuration")
        print("Check if RocketMQ containers are running on the server")
        return

    if args.json:
        print(json.dumps(detected, indent=2))

    if args.save:
        config_path = get_config_file_path()
        existing = load_config_from_file()

        # Merge detected into existing
        for key, value in detected.items():
            if 'rocketmq' not in existing:
                existing['rocketmq'] = {}
            existing['rocketmq'][key] = value

        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(existing, f, default_flow_style=False)

        print(f"Configuration saved to {config_path}")


if __name__ == '__main__':
    main_detect()