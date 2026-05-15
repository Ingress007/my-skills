"""工作空间管理 - 创建和管理部署工作目录"""

import os
import shutil
from pathlib import Path
from datetime import datetime


class WorkspaceManager:
    """管理本地工作空间的创建、切换和清理"""

    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir or os.path.expanduser("~/.app-deploy-ops"))
        self.workspaces_dir = self.base_dir / "workspaces"

    def create_workspace(self, env: str) -> Path:
        """创建新的部署工作空间

        Args:
            env: 环境名称 (prod/staging/test)

        Returns:
            工作空间路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        env_dir = self.workspaces_dir / env
        workspace_dir = env_dir / timestamp

        # 创建子目录
        dirs = [
            workspace_dir / "config",
            workspace_dir / "config/systemd",
            workspace_dir / "artifacts",
            workspace_dir / "logs",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

        # 更新 current 软链接
        current_link = env_dir / "current"
        if current_link.exists():
            current_link.unlink()
        # Windows 上使用 junction 或目录链接
        try:
            os.symlink(str(timestamp), str(current_link),
                       target_is_directory=True)
        except (OSError, NotImplementedError):
            # 不支持软链接则跳过
            pass

        return workspace_dir

    def get_current_workspace(self, env: str) -> Path:
        """获取当前工作空间路径"""
        current_link = self.workspaces_dir / env / "current"
        if current_link.exists():
            target = os.readlink(str(current_link))
            return self.workspaces_dir / env / target
        return None

    def list_workspaces(self, env: str) -> list:
        """列出环境的所有部署记录"""
        env_dir = self.workspaces_dir / env
        if not env_dir.exists():
            return []
        workspaces = []
        for item in env_dir.iterdir():
            if item.is_dir() and item.name != "current":
                workspaces.append(item)
        return sorted(workspaces, reverse=True)

    def cleanup_old_workspaces(self, env: str, keep: int = 10):
        """清理旧的部署工作空间"""
        workspaces = self.list_workspaces(env)
        for ws in workspaces[keep:]:
            shutil.rmtree(str(ws))