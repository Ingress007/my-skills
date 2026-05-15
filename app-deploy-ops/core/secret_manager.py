"""环境配置管理 - 单文件 environment.yaml 模板生成、填写检测、变量合并"""

import os
from pathlib import Path

import yaml


# 环境配置文件模板（单文件结构）
# 顶层键会覆盖 preset.variables 中的同名变量，优先级最高
# mysql/redis/rabbitmq 嵌套结构保持与模板引用一致
ENVIRONMENT_TEMPLATE = """
# ============================================================
# 环境配置文件 — 部署前请填写所有带空值的字段
# 此文件中的值会覆盖 preset 中的同名变量
# ============================================================

# ── 数据库 ──
db_host: 127.0.0.1
db_port: 3306
db_name: app_db
mysql:
  root_password: ""            # 必填：MySQL root 密码
  app_user: "app_user"         # 必填：应用数据库用户
  app_password: ""             # 必填：应用数据库密码
  database: "app_db"

# ── Redis ──
redis_host: 127.0.0.1
redis_port: 6379
redis:
  password: ""                 # 必填：Redis 密码

# ── 应用 ──
app_port: 8080
log_level: INFO

# ── RabbitMQ（微服务场景需要） ──
rabbitmq:
  user: ""
  password: ""

# ── 应用密钥 ──
jwt_secret: ""
api_key: ""

# ── Nginx SSL（可选） ──
ssl_enabled: false
# ssl_cert_path: /etc/nginx/ssl/cert.pem
# ssl_key_path: /etc/nginx/ssl/key.pem
""".lstrip()


class SecretManager:
    """管理环境配置文件的生成、检测和读取"""

    REQUIRED_FIELDS = [
        "mysql.root_password",
        "mysql.app_user",
        "mysql.app_password",
        "mysql.database",
        "redis.password",
    ]

    def __init__(self, secrets_dir: str = None):
        self.secrets_dir = Path(
            secrets_dir or os.path.expanduser("~/.app-deploy-ops/secrets")
        )
        self.env_file_name = "environment.yaml"

    def init_secrets(self, env: str) -> Path:
        """初始化环境配置目录，生成 environment.yaml 模板

        Args:
            env: 环境名称

        Returns:
            secrets 目录路径
        """
        env_secrets_dir = self.secrets_dir / env
        env_secrets_dir.mkdir(parents=True, exist_ok=True)

        # 创建 SSL 目录
        ssl_dir = env_secrets_dir / "ssl"
        ssl_dir.mkdir(exist_ok=True)

        # 生成 environment.yaml（不覆盖已有）
        filepath = env_secrets_dir / self.env_file_name
        if not filepath.exists():
            filepath.write_text(ENVIRONMENT_TEMPLATE, encoding="utf-8")

        return env_secrets_dir

    def check_secrets_filled(self, env: str) -> tuple:
        """检测环境配置是否已填写完整

        Args:
            env: 环境名称

        Returns:
            (是否完整, 未填写的字段路径列表)
        """
        env_secrets_dir = self.secrets_dir / env
        if not env_secrets_dir.exists():
            return False, ["环境配置目录不存在"]

        filepath = env_secrets_dir / self.env_file_name
        if not filepath.exists():
            return False, [f"{self.env_file_name} (文件不存在)"]

        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        unfilled = []
        for field_path in self.REQUIRED_FIELDS:
            value = self._get_nested(data, field_path)
            if value is None or value == "":
                unfilled.append(f"{field_path} (未填写)")

        return len(unfilled) == 0, unfilled

    def load_secrets(self, env: str) -> dict:
        """加载环境的所有配置

        Args:
            env: 环境名称

        Returns:
            环境配置字典（会与 preset.variables 合并，优先级更高）
        """
        env_secrets_dir = self.secrets_dir / env
        merged = {}

        if not env_secrets_dir.exists():
            return merged

        filepath = env_secrets_dir / self.env_file_name
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            merged.update(data)

        return merged

    @staticmethod
    def _get_nested(data: dict, path: str):
        """通过点号路径获取嵌套字典值，如 'mysql.root_password'"""
        keys = path.split(".")
        current = data
        for key in keys:
            if not isinstance(current, dict):
                return None
            current = current.get(key)
            if current is None:
                return None
        return current

    @staticmethod
    def _has_empty_value(data, depth: int = 0) -> bool:
        """递归检查字典中是否存在空值（兼容旧版，仅用于现有测试）"""
        if depth > 10:
            return False
        if isinstance(data, dict):
            for v in data.values():
                if SecretManager._has_empty_value(v, depth + 1):
                    return True
            return False
        return data is None or data == "" or data == []