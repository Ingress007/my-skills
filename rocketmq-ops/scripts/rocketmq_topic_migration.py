#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RocketMQ Topic Migration Script
支持配置化：环境变量 > 命令行 > 配置文件 > 默认值
"""

import argparse
import subprocess
import json
import re
import sys
import io
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# 修复 Windows 终端中文编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 导入配置模块
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)
from rocketmq_config import get_rocketmq_config, get_mqadmin_path, RocketMQConfig

# 系统topic过滤列表（无需迁移）
SYSTEM_TOPIC_PATTERNS = [
    r'^%RETRY%',
    r'^%DLQ%',
    r'^rmq_sys_',
    r'^DefaultCluster',
    r'^broker-',
    r'^OFFSET_MOVED',
    r'^TRANS_CHECK',
    r'^TBW102',
    r'^SELF_TEST',
    r'^SCHEDULE_TOPIC',
    r'^BenchmarkTest',
    r'^RMQ_SYS',
    r'^TopicTest',
]


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


def is_system_topic(topic_name: str) -> bool:
    """判断是否为系统topic"""
    for pattern in SYSTEM_TOPIC_PATTERNS:
        if re.match(pattern, topic_name):
            return True
    return False


def export_topics(source_server: str, config: RocketMQConfig) -> List[str]:
    """从源服务器导出业务topic列表"""
    mqadmin = get_mqadmin_path(config.paths.namesrv_container)
    result = run_ssh_command(
        source_server,
        f'{mqadmin} topicList -n {config.paths.namesrv_addr}'
    )

    if result.get('exit_code', 0) != 0:
        print(f"Error: 无法获取topic列表 - {result.get('stderr', 'Unknown error')}")
        sys.exit(1)

    topics: List[str] = []
    for line in result['stdout'].strip().split('\n'):
        topic = line.strip()
        if topic and not is_system_topic(topic):
            topics.append(topic)

    return topics


def get_topic_config(source_server: str, topic: str, config: RocketMQConfig) -> Dict[str, Any]:
    """获取topic详细配置"""
    mqadmin = get_mqadmin_path(config.paths.broker_container)
    result = run_ssh_command(
        source_server,
        f'{mqadmin} topicRoute -n {config.paths.namesrv_addr} -t {topic}'
    )

    # 使用配置默认值
    topic_config: Dict[str, Any] = {
        'name': topic,
        'readQueueNums': config.topics.read_queue,
        'writeQueueNums': config.topics.write_queue,
        'perm': config.topics.perm
    }

    # 尝试解析实际配置
    stdout = result.get('stdout', '')
    if 'readQueueNums' in stdout:
        match = re.search(r'"readQueueNums":(\d+)', stdout)
        if match:
            topic_config['readQueueNums'] = int(match.group(1))
        match = re.search(r'"writeQueueNums":(\d+)', stdout)
        if match:
            topic_config['writeQueueNums'] = int(match.group(1))
        match = re.search(r'"perm":(\d+)', stdout)
        if match:
            topic_config['perm'] = int(match.group(1))

    return topic_config


def create_topic(
    target_server: str,
    topic_config: Dict[str, Any],
    config: RocketMQConfig,
    message_type: Optional[str] = None
) -> bool:
    """在目标服务器创建topic"""
    mqadmin = get_mqadmin_path(config.paths.broker_container)
    mt = message_type or config.topics.message_type
    cmd = (
        f'{mqadmin} updateTopic -n {config.paths.namesrv_addr} '
        f'-t {topic_config["name"]} -c {config.paths.cluster_name} '
        f'-r {topic_config["readQueueNums"]} -w {topic_config["writeQueueNums"]} '
        f'-p {topic_config["perm"]} -a "+message.type={mt}"'
    )

    result = run_ssh_command(target_server, cmd)

    if result.get('exit_code', 0) != 0:
        print(f"  ✗ 创建失败: {result.get('stderr', 'Unknown error')}")
        return False

    if 'success' in result.get('stdout', '').lower():
        return True

    return False


def verify_topic(target_server: str, topic: str, config: RocketMQConfig) -> bool:
    """验证topic是否已创建"""
    mqadmin = get_mqadmin_path(config.paths.namesrv_container)
    result = run_ssh_command(
        target_server,
        f'{mqadmin} topicRoute -n {config.paths.namesrv_addr} -t {topic}'
    )

    return result.get('exit_code', 0) == 0 and 'queueDatas' in result.get('stdout', '')


def main() -> None:
    parser = argparse.ArgumentParser(description='RocketMQ Topic Migration Script')

    # 基本参数
    parser.add_argument('--source', required=True, help='源服务器 SSH alias')
    parser.add_argument('--target', required=True, help='目标服务器 SSH alias')

    # 自动检测参数
    parser.add_argument('--auto-detect', action='store_true',
                        help='自动从 Docker 检测配置（容器名、mqadmin路径、集群名）')

    # 配置覆盖参数（手动指定时使用）
    parser.add_argument('--mqadmin-path', help='覆盖 mqadmin 路径')
    parser.add_argument('--namesrv-container', help='NameServer 容器名')
    parser.add_argument('--broker-container', help='Broker 容器名')
    parser.add_argument('--cluster', help='目标集群名称')

    # 其他参数
    parser.add_argument('--dry-run', action='store_true', help='只导出不创建')
    parser.add_argument('--topics-file', help='从文件读取topic列表')
    parser.add_argument('--verify', action='store_true', help='迁移后验证')

    args = parser.parse_args()

    # 构建配置
    cli_overrides: Dict[str, Any] = {}
    if args.mqadmin_path:
        cli_overrides['mqadmin_path'] = args.mqadmin_path
    if args.namesrv_container:
        cli_overrides['namesrv_container'] = args.namesrv_container
    if args.broker_container:
        cli_overrides['broker_container'] = args.broker_container
    if args.cluster:
        cli_overrides['cluster_name'] = args.cluster

    # 获取配置（支持自动检测）
    auto_detect_server = args.source if args.auto_detect else None
    config = get_rocketmq_config(cli_overrides, auto_detect_server)

    print("=" * 60)
    print("RocketMQ Topic Migration")
    print("=" * 60)
    print(f"源服务器: {args.source}")
    print(f"目标服务器: {args.target}")
    if args.auto_detect:
        print("配置模式: 自动检测")
    print(f"集群: {config.paths.cluster_name}")
    print(f"NameServer: {config.paths.namesrv_container}")
    print(f"Broker: {config.paths.broker_container}")
    print()

    # 1. 导出topic列表
    print("[Step 1] 导出源服务器业务 topic...")

    if args.topics_file:
        with open(args.topics_file, 'r') as f:
            topics = [line.strip() for line in f if line.strip() and not is_system_topic(line.strip())]
    else:
        topics = export_topics(args.source, config)

    print(f"发现 {len(topics)} 个业务 topic")
    print()

    # 2. 显示topic列表
    print("[Step 2] Topic 列表:")
    for i, topic in enumerate(topics, 1):
        print(f"  {i:3}. {topic}")
    print()

    if args.dry_run:
        print("[Dry Run] 仅导出，不创建 topic")
        print("如需迁移，请去掉 --dry-run 参数")
        return

    # 3. 创建topic
    print("[Step 3] 在目标服务器创建 topic...")

    success_count = 0
    failed_count = 0

    for i, topic in enumerate(topics, 1):
        print(f"  [{i}/{len(topics)}] 创建: {topic}")

        topic_config = get_topic_config(args.source, topic, config)

        if create_topic(args.target, topic_config, config):
            success_count += 1
            print(f"  ✓ 成功")
        else:
            failed_count += 1

    print()

    # 4. 结果汇总
    print("[Step 4] 迁移结果:")
    print(f"  成功: {success_count}")
    print(f"  失败: {failed_count}")
    print()

    # 5. 验证
    if args.verify:
        print("[Step 5] 验证迁移结果...")
        verified = 0
        for topic in topics:
            if verify_topic(args.target, topic, config):
                verified += 1
        print(f"  已验证: {verified}/{len(topics)}")

    print("=" * 60)
    print("迁移完成!")

    if failed_count > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()