#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RocketMQ Topic Verification Script
核对源服务器和目标服务器的 topic 是否一致
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

# 系统topic过滤列表
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
    project_root = script_dir.parent.parent.parent
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


def get_topic_list(server: str, config: RocketMQConfig) -> List[str]:
    """获取服务器的业务topic列表"""
    mqadmin = get_mqadmin_path(config.paths.namesrv_container)
    result = run_ssh_command(
        server,
        f'{mqadmin} topicList -n {config.paths.namesrv_addr}'
    )

    if result.get('exit_code', 0) != 0:
        print(f"Error: 无法获取 {server} 的topic列表")
        sys.exit(1)

    topics: List[str] = []
    for line in result['stdout'].strip().split('\n'):
        topic = line.strip()
        if topic and not is_system_topic(topic):
            topics.append(topic)

    return sorted(topics)


def get_topic_config(server: str, topic: str, config: RocketMQConfig) -> Dict[str, Any]:
    """获取topic详细配置"""
    mqadmin = get_mqadmin_path(config.paths.broker_container)
    result = run_ssh_command(
        server,
        f'{mqadmin} topicRoute -n {config.paths.namesrv_addr} -t {topic}'
    )

    # 使用配置默认值
    topic_config: Dict[str, Any] = {
        'readQueueNums': config.topics.read_queue,
        'writeQueueNums': config.topics.write_queue,
        'perm': config.topics.perm,
        'messageType': 'UNSPECIFIED'
    }

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

    # 检查 message.type 属性
    if 'message.type=NORMAL' in stdout or '+message.type=NORMAL' in stdout:
        topic_config['messageType'] = 'NORMAL'

    return topic_config


def format_perm(perm: int) -> str:
    """格式化权限显示"""
    perms: List[str] = []
    if perm & 2:
        perms.append('W')
    if perm & 4:
        perms.append('R')
    return ''.join(perms) or '-'


def main() -> None:
    parser = argparse.ArgumentParser(description='RocketMQ Topic Verification Script')
    parser.add_argument('--source', required=True, help='源服务器 SSH alias')
    parser.add_argument('--target', required=True, help='目标服务器 SSH alias')

    # 自动检测参数
    parser.add_argument('--auto-detect', action='store_true',
                        help='自动从 Docker 检测配置')

    # 配置覆盖参数
    parser.add_argument('--mqadmin-path', help='覆盖 mqadmin 路径')
    parser.add_argument('--namesrv-container', help='NameServer 容器名')
    parser.add_argument('--broker-container', help='Broker 容器名')

    # 其他参数
    parser.add_argument('--detail', action='store_true', help='显示详细配置对比')
    parser.add_argument('--json', action='store_true', help='输出JSON格式结果')

    args = parser.parse_args()

    # 构建配置
    cli_overrides: Dict[str, Any] = {}
    if args.mqadmin_path:
        cli_overrides['mqadmin_path'] = args.mqadmin_path
    if args.namesrv_container:
        cli_overrides['namesrv_container'] = args.namesrv_container
    if args.broker_container:
        cli_overrides['broker_container'] = args.broker_container

    # 获取配置（支持自动检测）
    auto_detect_server = args.source if args.auto_detect else None
    config = get_rocketmq_config(cli_overrides, auto_detect_server)

    print("=" * 70)
    print("RocketMQ Topic Verification")
    print("=" * 70)
    print(f"源服务器: {args.source}")
    print(f"目标服务器: {args.target}")
    if args.auto_detect:
        print("配置模式: 自动检测")
    print()

    # 1. 获取两台服务器的topic列表
    print("[Step 1] 获取 topic 列表...")
    source_topics = get_topic_list(args.source, config)
    target_topics = get_topic_list(args.target, config)

    print(f"源服务器业务 topic: {len(source_topics)} 个")
    print(f"目标服务器业务 topic: {len(target_topics)} 个")
    print()

    # 2. 对比分析
    source_set = set(source_topics)
    target_set = set(target_topics)

    matched = sorted(source_set & target_set)  # 两边都有
    missing = sorted(source_set - target_set)   # 源有目标没有
    extra = sorted(target_set - source_set)     # 目标有源没有
    config_diff: List[Dict[str, Any]] = []

    print("[Step 2] 对比结果")
    print("-" * 70)

    # 3. 显示结果
    print(f"✓ 匹配的 topic: {len(matched)} 个")
    if args.detail and matched:
        for topic in matched:
            print(f"    {topic}")

    print()
    print(f"✗ 源服务器有但目标服务器缺少: {len(missing)} 个")
    if missing:
        for topic in missing:
            print(f"    {topic}")
        print()
        print("  建议: 运行迁移脚本创建这些 topic")

    print()
    print(f"✗ 目标服务器有但源服务器没有: {len(extra)} 个")
    if extra:
        for topic in extra:
            print(f"    {topic}")

    print()
    print("=" * 70)

    # 4. 详细配置对比
    if args.detail and matched:
        print()
        print("[Step 3] 详细配置对比")
        print("-" * 70)
        print(f"{'Topic':<40} {'源队列':<12} {'目标队列':<12} {'源类型':<10} {'目标类型':<10} {'状态'}")
        print("-" * 70)

        for topic in matched:
            src_config = get_topic_config(args.source, topic, config)
            tgt_config = get_topic_config(args.target, topic, config)

            # 对比配置
            queues_match = (
                src_config['readQueueNums'] == tgt_config['readQueueNums'] and
                src_config['writeQueueNums'] == tgt_config['writeQueueNums']
            )
            type_match = src_config['messageType'] == tgt_config['messageType']

            status = '✓' if queues_match and type_match else '⚠'

            if not queues_match or not type_match:
                config_diff.append({
                    'topic': topic,
                    'source': src_config,
                    'target': tgt_config
                })

            src_queues = f"{src_config['readQueueNums']}/{src_config['writeQueueNums']}"
            tgt_queues = f"{tgt_config['readQueueNums']}/{tgt_config['writeQueueNums']}"

            print(f"{topic:<40} {src_queues:<12} {tgt_queues:<12} {src_config['messageType']:<10} {tgt_config['messageType']:<10} {status}")

        print("-" * 70)

        if config_diff:
            print()
            print(f"⚠ 发现 {len(config_diff)} 个配置不一致的 topic")
        else:
            print()
            print("✓ 所有匹配 topic 配置一致")

    # 5. 最终结果
    print()
    print("=" * 70)
    print("核对结果汇总")
    print("=" * 70)

    if missing:
        print(f"[缺少] {len(missing)} 个 topic 需要迁移")
        print("  命令: python rocketmq-ops/scripts/rocketmq_topic_migration.py")
        print(f"        --source {args.source} --target {args.target}")

    if config_diff and args.detail:
        print(f"[配置差异] {len(config_diff)} 个 topic 配置不一致")

    if not missing and not config_diff:
        print("✓ 迁移完成，topic 完全一致!")

    # JSON 输出
    if args.json:
        print()
        result: Dict[str, Any] = {
            'source': args.source,
            'target': args.target,
            'source_count': len(source_topics),
            'target_count': len(target_topics),
            'matched': matched,
            'missing': missing,
            'extra': extra,
            'config_diff': config_diff if args.detail else None,
            'status': 'complete' if not missing and not config_diff else 'incomplete'
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))

    # 返回状态码
    if missing:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()