"""app-deploy-ops 测试套件"""

import unittest
import tempfile
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestWorkspace(unittest.TestCase):
    """测试工作空间管理"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.orig_dir = os.environ.get("HOME")
        os.environ["HOME"] = self.temp_dir

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
        if self.orig_dir:
            os.environ["HOME"] = self.orig_dir

    def test_create_workspace(self):
        """测试创建工作空间"""
        from core.workspace import WorkspaceManager

        wm = WorkspaceManager()
        workspace_dir = wm.create_workspace("test-env")

        self.assertTrue(workspace_dir.exists())
        self.assertTrue((workspace_dir / "config").exists())
        self.assertTrue((workspace_dir / "artifacts").exists())
        self.assertTrue((workspace_dir / "logs").exists())

    def test_list_workspaces(self):
        """测试列出工作空间"""
        from core.workspace import WorkspaceManager

        wm = WorkspaceManager()
        wm.create_workspace("test-env")
        wm.create_workspace("test-env")

        workspaces = wm.list_workspaces("test-env")
        self.assertEqual(len(workspaces), 2)


class TestSecretManager(unittest.TestCase):
    """测试环境配置管理"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.orig_dir = os.environ.get("HOME")
        os.environ["HOME"] = self.temp_dir

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
        if self.orig_dir:
            os.environ["HOME"] = self.orig_dir

    def test_init_secrets(self):
        """测试初始化环境配置目录"""
        from core.secret_manager import SecretManager

        sm = SecretManager(secrets_dir=self.temp_dir)
        secrets_dir = sm.init_secrets("test-env")

        self.assertTrue(secrets_dir.exists())
        self.assertTrue((secrets_dir / "environment.yaml").exists())
        self.assertTrue((secrets_dir / "ssl").exists())

    def test_check_secrets_unfilled(self):
        """测试检测未填写的环境配置"""
        from core.secret_manager import SecretManager

        sm = SecretManager(secrets_dir=self.temp_dir)
        sm.init_secrets("test-env")

        filled, unfilled = sm.check_secrets_filled("test-env")
        self.assertFalse(filled)
        self.assertTrue(len(unfilled) > 0)

    def test_check_secrets_filled(self):
        """测试检测部分填写的环境配置（仍应失败）"""
        from core.secret_manager import SecretManager
        import yaml

        sm = SecretManager(secrets_dir=self.temp_dir)
        sm.init_secrets("test-env")

        # 只填写部分必填字段（仍缺少 app_user / app_password / database）
        env_file = sm.secrets_dir / "test-env" / "environment.yaml"
        with open(env_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        data["mysql"]["root_password"] = "test_pass"
        data["redis"]["password"] = "test_redis_pass"
        with open(env_file, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

        filled, unfilled = sm.check_secrets_filled("test-env")
        self.assertFalse(filled)  # mysql.app_user, mysql.app_password, mysql.database 仍为空

    def test_check_secrets_all_filled(self):
        """测试全部必填字段已填写的环境配置"""
        from core.secret_manager import SecretManager
        import yaml

        sm = SecretManager(secrets_dir=self.temp_dir)
        sm.init_secrets("test-env")

        # 填写所有必填字段
        env_file = sm.secrets_dir / "test-env" / "environment.yaml"
        with open(env_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        data["mysql"]["root_password"] = "root_pass"
        data["mysql"]["app_user"] = "app_user"
        data["mysql"]["app_password"] = "app_pass"
        data["mysql"]["database"] = "app_db"
        data["redis"]["password"] = "redis_pass"
        with open(env_file, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

        filled, unfilled = sm.check_secrets_filled("test-env")
        self.assertTrue(filled, f"应全部通过，但未填写: {unfilled}")

    def test_load_secrets(self):
        """测试加载环境配置"""
        from core.secret_manager import SecretManager
        import yaml

        sm = SecretManager(secrets_dir=self.temp_dir)
        sm.init_secrets("test-env")

        # 填写一些值
        env_file = sm.secrets_dir / "test-env" / "environment.yaml"
        with open(env_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        data["mysql"]["root_password"] = "test_pass"
        data["mysql"]["app_user"] = "app_user"
        with open(env_file, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

        env_config = sm.load_secrets("test-env")
        self.assertIn("mysql", env_config)
        self.assertEqual(env_config["mysql"]["root_password"], "test_pass")
        self.assertEqual(env_config["db_host"], "127.0.0.1")  # 顶层变量也加载


class TestBuilder(unittest.TestCase):
    """测试构建工具检测"""

    def test_nodejs_check(self):
        """测试 Node.js 检测（不抛异常）"""
        from core.builder import NodeJSBuilder

        builder = NodeJSBuilder()
        # 只是测试不抛出异常
        installed = builder.check_installed()
        self.assertIsInstance(installed, bool)

    def test_maven_check(self):
        """测试 Maven 检测（不抛异常）"""
        from core.builder import MavenBuilder

        builder = MavenBuilder()
        installed = builder.check_installed()
        self.assertIsInstance(installed, bool)


class TestValidator(unittest.TestCase):
    """测试验证工具"""

    def test_port_check_invalid(self):
        """测试端口检查（无效地址）"""
        from core.validator import Validator

        v = Validator()
        result = v.check_port("192.0.2.1", 9999, timeout=2)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()