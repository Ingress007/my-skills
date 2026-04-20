#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RocketMQ Topic Migration Script
"""

import argparse
import subprocess
import json
import re
import sys
import io
from pathlib import Path

# 修复 Windows 终端中文编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

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

# 默认topic配置
DEFAULT_READ_QUEUE = 4
DEFAULT_WRITE_QUEUE = 4
DEFAULT_PERM = 6  # RW


def run_ssh_command(server_alias: str, command: str) -> dict:
    """通过 ssh_manager.py 执行远程命令"""
    # 获取项目根目录下的 ssh_manager.py
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


def get_mqadmin_path(container: str) -> str:
    """获取 mqadmin 命令路径"""
    return f'docker exec {container} /home/rocketmq/rocketmq-5.3.0/bin/mqadmin'


def is_system_topic(topic_name: str) -> bool:
    """判断是否为系统topic"""
    for pattern in SYSTEM_TOPIC_PATTERNS:
        if re.match(pattern, topic_name):
            return True
    return False


def export_topics(source_server: str, namesrv_container: str = 'rmqnamesrv') -> list:
    """从源服务器导出业务topic列表"""
    mqadmin = get_mqadmin_path(namesrv_container)
    result = run_ssh_command(source_server, f'{mqadmin} topicList -n localhost:9876')

    if result.get('exit_code', 0) != 0:
        print(f"Error: 无法获取topic列表 - {result.get('stderr', 'Unknown error')}")
        sys.exit(1)

    topics = []
    for line in result['stdout'].strip().split('\n'):
        topic = line.strip()
        if topic and not is_system_topic(topic):
            topics.append(topic)

    return topics


def get_topic_config(source_server: str, topic: str, broker_container: str = 'rmqbroker') -> dict:
    """获取topic详细配置"""
    mqadmin = get_mqadmin_path(broker_container)
    result = run_ssh_command(
        source_server,
        f'{mqadmin} topicRoute -n rmqnamesrv:9876 -t {topic}'
    )

    # 默认配置
    config = {
        'name': topic,
        'readQueueNums': DEFAULT_READ_QUEUE,
        'writeQueueNums': DEFAULT_WRITE_QUEUE,
        'perm': DEFAULT_PERM
    }

    # 尝试解析实际配置
    stdout = result.get('stdout', '')
    if 'readQueueNums' in stdout:
        match = re.search(r'"readQueueNums":(\d+)', stdout)
        if match:
            config['readQueueNums'] = int(match.group(1))
        match = re.search(r'"writeQueueNums":(\d+)', stdout)
        if match:
            config['writeQueueNums'] = int(match.group(1))
        match = re.search(r'"perm":(\d+)', stdout)
        if match:
            config['perm'] = int(match.group(1))

    return config


def create_topic(target_server: str, config: dict, broker_container: str = 'rmqbroker', cluster: str = 'DefaultCluster', message_type: str = 'NORMAL') -> bool:
    """在目标服务器创建topic"""
    mqadmin = get_mqadmin_path(broker_container)
    # 添加 message.type 属性，RocketMQ 5.x Dashboard 需要
    cmd = f'{mqadmin} updateTopic -n rmqnamesrv:9876 -t {config["name"]} -c {cluster} -r {config["readQueueNums"]} -w {config["writeQueueNums"]} -p {config["perm"]} -a "+message.type={message_type}"'

    result = run_ssh_command(target_server, cmd)

    if result.get('exit_code', 0) != 0:
        print(f"  ✗ 创建失败: {result.get('stderr', 'Unknown error')}")
        return False

    if 'success' in result.get('stdout', '').lower():
        return True

    return False


def verify_topic(target_server: str, topic: str, namesrv_container: str = 'rmqnamesrv') -> bool:
    """验证topic是否已创建"""
    mqadmin = get_mqadmin_path(namesrv_container)
    result = run_ssh_command(
        target_server,
        f'{mqadmin} topicRoute -n localhost:9876 -t {topic}'
    )

    return result.get('exit_code', 0) == 0 and 'queueDatas' in result.get('stdout', '')


def main():
    parser = argparse.ArgumentParser(description='RocketMQ Topic Migration Script')
    parser.add_argument('--source', required=True, help='源服务器 SSH alias')
    parser.add_argument('--target', required=True, help='目标服务器 SSH alias')
    parser.add_argument('--dry-run', action='store_true', help='只导出不创建')
    parser.add_argument('--topics-file', help='从文件读取topic列表')
    parser.add_argument('--cluster', default='DefaultCluster', help='目标集群名称')
    parser.add_argument('--verify', action='store_true', help='迁移后验证')

    args = parser.parse_args()

    print("=" * 60)
    print("RocketMQ Topic Migration")
    print("=" * 60)
    print(f"源服务器: {args.source}")
    print(f"目标服务器: {args.target}")
    print(f"集群: {args.cluster}")
    print()

    # 1. 导出topic列表
    print("[Step 1] 导出源服务器业务 topic...")

    if args.topics_file:
        with open(args.topics_file, 'r') as f:
            topics = [line.strip() for line in f if line.strip() and not is_system_topic(line.strip())]
    else:
        topics = export_topics(args.source)

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

        config = get_topic_config(args.source, topic)

        if create_topic(args.target, config, cluster=args.cluster):
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
            if verify_topic(args.target, topic):
                verified += 1
        print(f"  已验证: {verified}/{len(topics)}")

    print("=" * 60)
    print("迁移完成!")

    if failed_count > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()