"""本地构建工具 - 检测构建环境并执行构建"""

import os
import subprocess
import sys


class BuilderError(Exception):
    """构建相关异常"""
    pass


class NodeJSBuilder:
    """Node.js 前端构建"""

    @staticmethod
    def check_installed() -> bool:
        """检测 Node.js 是否已安装"""
        try:
            result = subprocess.run(["node", "--version"],
                                    capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    @staticmethod
    def get_version() -> str:
        """获取 Node.js 版本"""
        result = subprocess.run(["node", "--version"],
                                capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else ""

    def build(self, project_dir: str, output_dir: str) -> dict:
        """执行前端构建

        Args:
            project_dir: Vue 项目目录
            output_dir: 构建产物输出目录

        Returns:
            构建信息
        """
        if not self.check_installed():
            raise BuilderError(
                "Node.js 未安装，请先安装 Node.js")

        version = self.get_version()
        print(f"[Node.js] 版本: {version}")

        # 安装依赖
        print("[Node.js] npm install ...")
        result = subprocess.run(["npm", "install"],
                                cwd=project_dir,
                                capture_output=True, text=True)
        if result.returncode != 0:
            raise BuilderError(f"npm install 失败:\n{result.stderr}")

        # 执行构建
        print("[Node.js] npm run build ...")
        result = subprocess.run(["npm", "run", "build"],
                                cwd=project_dir,
                                capture_output=True, text=True)
        if result.returncode != 0:
            raise BuilderError(f"npm run build 失败:\n{result.stderr}")

        # 复制产物到输出目录
        dist_dir = os.path.join(project_dir, "dist")
        if os.path.exists(dist_dir):
            import shutil
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)
            shutil.copytree(dist_dir, output_dir)

        files_count = len(os.listdir(output_dir)) if os.path.exists(output_dir) else 0

        return {
            "type": "frontend",
            "node_version": version,
            "output": output_dir,
            "files_count": files_count,
        }


class MavenBuilder:
    """Maven Java 后端构建"""

    @staticmethod
    def check_installed() -> bool:
        """检测 Maven 是否已安装"""
        try:
            result = subprocess.run(["mvn", "--version"],
                                    capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    @staticmethod
    def get_version() -> str:
        """获取 Maven 版本"""
        result = subprocess.run(["mvn", "--version"],
                                capture_output=True, text=True)
        lines = result.stdout.splitlines()
        return lines[0].strip() if lines else ""

    def build(self, project_dir: str, output_dir: str,
              profile: str = None, skip_tests: bool = True) -> dict:
        """执行 Maven 构建

        Args:
            project_dir: Maven 项目目录
            output_dir: JAR 输出目录
            profile: Maven profile
            skip_tests: 是否跳过测试

        Returns:
            构建信息
        """
        if not self.check_installed():
            raise BuilderError(
                "Maven 未安装，请先安装 Maven")

        version = self.get_version()
        print(f"[Maven] 版本: {version}")

        # 构建命令
        cmd = ["mvn", "clean", "package"]
        if skip_tests:
            cmd.append("-DskipTests")
        if profile:
            cmd.extend(["-P", profile])

        print(f"[Maven] {' '.join(cmd)} ...")
        result = subprocess.run(cmd, cwd=project_dir,
                                capture_output=True, text=True)
        if result.returncode != 0:
            raise BuilderError(f"Maven 构建失败:\n{result.stderr}")

        # 查找生成的 JAR 包
        import glob
        target_dir = os.path.join(project_dir, "target")
        jar_files = glob.glob(os.path.join(target_dir, "*.jar"))

        if not jar_files:
            raise BuilderError("未找到构建产物 JAR 包")

        # 复制到输出目录
        import shutil
        src_jar = jar_files[0]
        dest_jar = os.path.join(output_dir, os.path.basename(src_jar))
        os.makedirs(output_dir, exist_ok=True)
        shutil.copy2(src_jar, dest_jar)

        jar_size = os.path.getsize(dest_jar)

        return {
            "type": "backend",
            "maven_version": version,
            "jar": dest_jar,
            "size": f"{jar_size / 1024 / 1024:.1f} MB",
        }
