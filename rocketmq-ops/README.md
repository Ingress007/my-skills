# RocketMQ Ops

RocketMQ topic migration and verification skill for AI Agents.

## Features

| Feature | Description |
|---------|-------------|
| Topic Migration | Export topics from source, create on target with NORMAL type |
| Topic Verification | Compare servers, detect missing/extra topics, detail config diff |
| Auto-Detect | Automatically detect Docker containers, mqadmin path, cluster name |
| Dry Run Mode | Preview before migration |
| System Filter | Auto-filter %RETRY%, %DLQ%, rmq_sys_* |
| Windows Support | UTF-8 encoding fix for Chinese output |

## Quick Start

```bash
# Install dependencies
pip install paramiko pyyaml

# Auto-detect configuration from Docker
python rocketmq-ops/scripts/rocketmq_config.py 服务器别名 --save

# Preview topics with auto-detect (dry-run)
python rocketmq-ops/scripts/rocketmq_topic_migration.py \
  --source 源服务器 --target 目标服务器 --auto-detect --dry-run

# Execute migration with auto-detect
python rocketmq-ops/scripts/rocketmq_topic_migration.py \
  --source 源服务器 --target 目标服务器 --auto-detect

# Verify results
python rocketmq-ops/scripts/rocketmq_topic_verification.py \
  --source 源服务器 --target 目标服务器 --auto-detect --detail
```

## Auto-Detect Configuration

**Detects from Docker containers:**
- `namesrv_container` - NameServer container name
- `broker_container` - Broker container name
- `mqadmin_path` - mqadmin tool path inside container
- `cluster_name` - RocketMQ cluster name

```bash
# Detect and display
python rocketmq-ops/scripts/rocketmq_config.py 服务器别名

# Detect and save to config.yaml
python rocketmq-ops/scripts/rocketmq_config.py 服务器别名 --save

# Output as JSON
python rocketmq-ops/scripts/rocketmq_config.py 服务器别名 --json
```

## Scripts

### rocketmq_topic_migration.py

Topic migration script.

| Argument | Description |
|----------|-------------|
| `--source` | Source server SSH alias (required) |
| `--target` | Target server SSH alias (required) |
| `--auto-detect` | Auto-detect config from Docker |
| `--dry-run` | Preview only, no creation |
| `--verify` | Verify after migration |
| `--topics-file` | Read topics from file |
| `--mqadmin-path` | Override mqadmin path |
| `--cluster` | Override cluster name |

**Examples:**
```bash
# Auto-detect mode (recommended)
python scripts/rocketmq_topic_migration.py \
  --source prod-server --target test-server --auto-detect

# Manual config mode
python scripts/rocketmq_topic_migration.py \
  --source prod-server --target test-server \
  --mqadmin-path /custom/path --broker-container mybroker
```

### rocketmq_topic_verification.py

Topic verification and comparison script.

| Argument | Description |
|----------|-------------|
| `--source` | Source server SSH alias (required) |
| `--target` | Target server SSH alias (required) |
| `--auto-detect` | Auto-detect config from Docker |
| `--detail` | Show detailed config comparison |
| `--json` | Output in JSON format |

## Configuration Priority

**4-level priority**: CLI > Auto-detect > Config file > Default

```bash
# CLI argument override (highest priority)
python scripts/rocketmq_topic_migration.py \
  --source s1 --target s2 --auto-detect \
  --cluster MyCluster
```

## Typical Workflow

```bash
# Step 1: Auto-detect and save config
python rocketmq-ops/scripts/rocketmq_config.py \
  交付测试服务器 --save

# Step 2: Preview with auto-detect
python rocketmq-ops/scripts/rocketmq_topic_migration.py \
  --source 交付测试服务器 --target 筷电猫测试服务器 --auto-detect --dry-run

# Step 3: Migrate with auto-detect
python rocketmq-ops/scripts/rocketmq_topic_migration.py \
  --source 交付测试服务器 --target 筷电猫测试服务器 --auto-detect

# Step 4: Verify
python rocketmq-ops/scripts/rocketmq_topic_verification.py \
  --source 交付测试服务器 --target 筷电猫测试服务器 --auto-detect --detail
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

## Troubleshooting

### UNSPECIFIED type in Dashboard

RocketMQ Dashboard 2.0+ requires explicit message type. This script adds `-a '+message.type=NORMAL'` automatically.

### Auto-detect fails

Check if RocketMQ containers are running:
```bash
docker ps --format '{{.Names}} {{.Image}}'
```

Container names should contain `namesrv` or `broker`, or use `rmqnamesrv`/`rmqbroker` pattern.