---
name: rocketmq-ops
description: "RocketMQ topic migration and management skill for AI Agents. Export topics from source server, create topics on target server with NORMAL type, verify migration results with detailed comparison."
---

# RocketMQ Ops Skill

This skill provides RocketMQ topic migration and management capabilities for AI Agents.

## Features

- **Topic Migration**: Export and create topics with NORMAL type (RocketMQ 5.x compatible)
- **Topic Verification**: Compare source and target servers, detect missing/extra topics
- **Auto-Detect**: Automatically detect Docker containers, mqadmin path, cluster name
- **Dry Run Mode**: Preview topics before migration
- **Detailed Comparison**: Compare queue numbers, permissions, message types
- **Safety First**: Auto-filter system topics (%RETRY%, %DLQ%, rmq_sys_*)

## Prerequisites

1. SSH config configured with source and target servers
2. RocketMQ 5.x installed on both servers (Docker containers: namesrv + broker)
3. Python dependencies:
```bash
pip install paramiko pyyaml
```

## Scripts

| Script | Function |
|--------|----------|
| `rocketmq_topic_migration.py` | Topic migration from source to target |
| `rocketmq_topic_verification.py` | Verify and compare topics between servers |
| `rocketmq_config.py` | Configuration management + auto-detect CLI |

## Usage

### 1. Auto-Detect Configuration (Recommended for Docker)

Automatically detect RocketMQ configuration from Docker containers:

```bash
# Detect and display configuration
python rocketmq-ops/scripts/rocketmq_config.py 服务器别名

# Detect and save to config.yaml
python rocketmq-ops/scripts/rocketmq_config.py 服务器别名 --save
```

**Auto-detects:**
- Container names (namesrv_container, broker_container)
- mqadmin path inside container
- Cluster name
- NameServer address

### 2. Topic Migration

**Auto-detect mode (recommended):**
```bash
python rocketmq-ops/scripts/rocketmq_topic_migration.py \
  --source 源服务器别名 \
  --target 目标服务器别名 \
  --auto-detect
```

**Basic migration:**
```bash
python rocketmq-ops/scripts/rocketmq_topic_migration.py \
  --source 源服务器别名 \
  --target 目标服务器别名
```

**Dry run (preview only):**
```bash
python rocketmq-ops/scripts/rocketmq_topic_migration.py \
  --source 源服务器别名 \
  --target 目标服务器别名 \
  --auto-detect \
  --dry-run
```

**With post-verification:**
```bash
python rocketmq-ops/scripts/rocketmq_topic_migration.py \
  --source 源服务器别名 \
  --target 目标服务器别名 \
  --auto-detect \
  --verify
```

**From topics file:**
```bash
# Create topics.txt with topic names (one per line)
python rocketmq-ops/scripts/rocketmq_topic_migration.py \
  --source 源服务器别名 \
  --target 目标服务器别名 \
  --topics-file topics.txt
```

### 2. Topic Verification

**Basic verification:**
```bash
python rocketmq-ops/scripts/rocketmq_topic_verification.py \
  --source 源服务器别名 \
  --target 目标服务器别名
```

**Detailed comparison:**
```bash
python rocketmq-ops/scripts/rocketmq_topic_verification.py \
  --source 源服务器别名 \
  --target 目标服务器别名 \
  --detail
```

**JSON output:**
```bash
python rocketmq-ops/scripts/rocketmq_topic_verification.py \
  --source 源服务器别名 \
  --target 目标服务器别名 \
  --json
```

## Topic Configuration

Default configuration for migrated topics:
- Read Queue Num: 4
- Write Queue Num: 4
- Permission: 6 (RW)
- Message Type: NORMAL (RocketMQ 5.x Dashboard compatible)

## System Topics Filter

These topics are automatically filtered (not migrated):
- `%RETRY%*` - Retry topics
- `%DLQ%*` - Dead letter queue topics
- `rmq_sys_*` - RocketMQ system topics
- `DefaultCluster`, `broker-*` - Cluster/Broker info
- `TBW102`, `SELF_TEST`, `OFFSET_MOVED`, `TRANS_CHECK` - Internal topics
- `SCHEDULE_TOPIC_XXXX`, `RMQ_SYS_TRANS_HALF_TOPIC` - Transaction topics

## Output Examples

### Migration Output

```
============================================================
RocketMQ Topic Migration
============================================================
源服务器: 交付测试服务器
目标服务器: 筷电猫测试服务器

[Step 1] 导出源服务器业务 topic...
发现 43 个业务 topic

[Step 2] Topic 列表:
    1. iot-saas-device-log-topic
    2. ORDER_CREATE_TOPIC
    ...

[Step 3] 在目标服务器创建 topic...
  [1/43] 创建: iot-saas-device-log-topic
  ✓ 成功

[Step 4] 迁移结果:
  成功: 43
  失败: 0

============================================================
迁移完成!
```

### Verification Output

```
======================================================================
RocketMQ Topic Verification
======================================================================
源服务器: 交付测试服务器
目标服务器: 筷电猫测试服务器

[Step 1] 获取 topic 列表...
源服务器业务 topic: 43 个
目标服务器业务 topic: 43 个

[Step 2] 对比结果
----------------------------------------------------------------------
✓ 匹配的 topic: 43 个

✗ 源服务器有但目标服务器缺少: 0 个

✗ 目标服务器有但源服务器没有: 0 个

======================================================================
核对结果汇总
======================================================================
✓ 迁移完成，topic 完全一致!
```

### Verification with Detail

```
[Step 3] 详细配置对比
----------------------------------------------------------------------
Topic                                    源队列       目标队列     源类型     目标类型     状态
----------------------------------------------------------------------
ORDER_CREATE_TOPIC                       4/4          4/4          NORMAL     NORMAL      ✓
iot-saas-device-log-topic                4/4          4/4          NORMAL     NORMAL      ✓
...
----------------------------------------------------------------------
✓ 所有匹配 topic 配置一致
```

## Typical Workflow

```bash
# 1. Preview topics to migrate
python rocketmq-ops/scripts/rocketmq_topic_migration.py \
  --source 生产服务器 --target 测试服务器 --dry-run

# 2. Execute migration
python rocketmq-ops/scripts/rocketmq_topic_migration.py \
  --source 生产服务器 --target 测试服务器

# 3. Verify results
python rocketmq-ops/scripts/rocketmq_topic_verification.py \
  --source 生产服务器 --target 测试服务器 --detail
```

## Troubleshooting

### UNSPECIFIED vs NORMAL Type

RocketMQ Dashboard 2.0+ shows topic types:
- **UNSPECIFIED**: Created without type attribute (default)
- **NORMAL**: Created with `-a '+message.type=NORMAL'`

This script automatically sets NORMAL type for Dashboard compatibility.

### Windows Encoding Issues

The scripts handle Windows terminal encoding automatically. If you see garbled Chinese text, ensure your terminal supports UTF-8.