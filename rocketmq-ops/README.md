# RocketMQ Ops

RocketMQ topic migration and verification skill for AI Agents.

## Features

| Feature | Description |
|---------|-------------|
| Topic Migration | Export topics from source, create on target with NORMAL type |
| Topic Verification | Compare servers, detect missing/extra topics, detail config diff |
| Dry Run Mode | Preview before migration |
| System Filter | Auto-filter %RETRY%, %DLQ%, rmq_sys_* |
| Windows Support | UTF-8 encoding fix for Chinese output |

## Quick Start

```bash
# Install dependencies
pip install paramiko

# Preview topics (dry-run)
python rocketmq-ops/scripts/rocketmq_topic_migration.py \
  --source 源服务器 --target 目标服务器 --dry-run

# Execute migration
python rocketmq-ops/scripts/rocketmq_topic_migration.py \
  --source 源服务器 --target 目标服务器

# Verify results
python rocketmq-ops/scripts/rocketmq_topic_verification.py \
  --source 源服务器 --target 目标服务器 --detail
```

## Scripts

### rocketmq_topic_migration.py

Topic migration script.

| Argument | Description |
|----------|-------------|
| `--source` | Source server SSH alias (required) |
| `--target` | Target server SSH alias (required) |
| `--dry-run` | Preview only, no creation |
| `--verify` | Verify after migration |
| `--topics-file` | Read topics from file |
| `--cluster` | Target cluster name (default: DefaultCluster) |

**Examples:**
```bash
# Basic migration
python scripts/rocketmq_topic_migration.py --source prod-server --target test-server

# Dry run
python scripts/rocketmq_topic_migration.py --source prod-server --target test-server --dry-run

# From file
python scripts/rocketmq_topic_migration.py --source prod-server --target test-server --topics-file topics.txt
```

### rocketmq_topic_verification.py

Topic verification and comparison script.

| Argument | Description |
|----------|-------------|
| `--source` | Source server SSH alias (required) |
| `--target` | Target server SSH alias (required) |
| `--detail` | Show detailed config comparison |
| `--json` | Output in JSON format |

**Examples:**
```bash
# Basic verification
python scripts/rocketmq_topic_verification.py --source prod-server --target test-server

# Detailed comparison
python scripts/rocketmq_topic_verification.py --source prod-server --target test-server --detail

# JSON output
python scripts/rocketmq_topic_verification.py --source prod-server --target test-server --json
```

## Prerequisites

1. SSH config configured (`~/.ssh/config`)
2. RocketMQ 5.x on both servers (namesrv + broker containers)
3. Python + paramiko

```bash
pip install paramiko
```

## Typical Workflow

```bash
# Step 1: Preview
python rocketmq-ops/scripts/rocketmq_topic_migration.py \
  --source 交付测试服务器 --target 筷电猫测试服务器 --dry-run

# Step 2: Migrate
python rocketmq-ops/scripts/rocketmq_topic_migration.py \
  --source 交付测试服务器 --target 筷电猫测试服务器

# Step 3: Verify
python rocketmq-ops/scripts/rocketmq_topic_verification.py \
  --source 交付测试服务器 --target 筷电猫测试服务器 --detail
```

## Topic Configuration

Migrated topics use:
- **Queue**: 4 read / 4 write
- **Permission**: 6 (RW)
- **Type**: NORMAL (Dashboard 2.0+ compatible)

## System Topics Filtered

| Pattern | Description |
|---------|-------------|
| `%RETRY%*` | Retry topics |
| `%DLQ%*` | Dead letter queue |
| `rmq_sys_*` | System topics |
| `DefaultCluster` | Cluster info |
| `broker-*` | Broker metadata |
| `SCHEDULE_TOPIC_*` | Scheduled messages |

## Troubleshooting

### UNSPECIFIED type in Dashboard

RocketMQ Dashboard 2.0+ requires explicit message type. Topics created via `mqadmin` default to UNSPECIFIED.

**Solution**: This script adds `-a '+message.type=NORMAL'` automatically.

### Windows Chinese encoding

Scripts auto-fix UTF-8 output on Windows. If garbled, check terminal encoding support.