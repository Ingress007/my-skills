"""部署执行 - 编排完整的部署流程"""

import os
import json
from pathlib import Path

from .workspace import WorkspaceManager
from .secret_manager import SecretManager


class Deployer:
    """部署执行引擎"""

    def __init__(self, env: str, server: str, preset: str = "spring-boot-vue"):
        self.env = env
        self.server = server
        self.preset = preset

        self.workspace = WorkspaceManager()
        self.secrets = SecretManager()
        self.workspace_dir = None

        self._manifest = {
            "deploy_id": "",
            "env": env,
            "server": server,
            "preset": preset,
            "timestamp": "",
            "status": "pending",
            "steps": [],
        }

    def _log(self, msg: str):
        """记录日志"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {msg}"
        print(line)

        # 写入日志文件
        if self.workspace_dir:
            log_file = self.workspace_dir / "logs" / "deploy.log"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(line + "\n")

    def _step(self, name: str, status: str = "running", detail: str = ""):
        """记录步骤状态"""
        step = {
            "name": name,
            "status": status,
            "detail": detail,
        }
        self._manifest["steps"].append(step)
        return step

    def init(self) -> Path:
        """初始化工作空间和 secrets"""
        from datetime import datetime

        self._manifest["timestamp"] = datetime.now().isoformat()
        self._manifest["deploy_id"] = datetime.now().strftime("%Y%m%d_%H%M%S")

        self._log(f"初始化工作空间 (env={self.env})")
        self.workspace_dir = self.workspace.create_workspace(self.env)
        self._log(f"工作空间: {self.workspace_dir}")

        self._log(f"初始化 secrets 目录")
        secrets_dir = self.secrets.init_secrets(self.env)
        self._log(f"Secrets: {secrets_dir}")

        self._step("init", "completed",
                    f"工作空间: {self.workspace_dir}")
        return self.workspace_dir

    def check_secrets(self) -> bool:
        """检测敏感配置是否已填写"""
        self._log("检查敏感配置...")
        filled, unfilled = self.secrets.check_secrets_filled(self.env)

        if not filled:
            self._log(f"敏感配置未完成，缺少: {unfilled}")
            self._step("check_secrets", "failed",
                       f"未填写: {', '.join(unfilled)}")
            return False

        self._log("敏感配置检查通过")
        self._step("check_secrets", "completed")
        return True

    def prepare_config(self, preset_config: dict,
                       template_dir: str) -> list:
        """渲染配置文件

        Args:
            preset_config: 预设配置字典
            template_dir: 模板目录路径

        Returns:
            生成的配置文件列表
        """
        from jinja2 import Environment, FileSystemLoader, Undefined

        config_dir = self.workspace_dir / "config"
        systemd_dir = config_dir / "systemd"
        systemd_dir.mkdir(parents=True, exist_ok=True)

        secrets_vars = self.secrets.load_secrets(self.env)

        # 合并普通变量和敏感变量（敏感变量优先）
        variables = {}
        variables.update(preset_config.get("variables", {}))

        # 注入结构化数据供模板使用（nginx_routes, backend_services 等）
        nginx_routes = preset_config.get("nginx", {}).get("routes", [])
        if nginx_routes:
            variables["nginx_routes"] = nginx_routes
        backend_services = preset_config.get("backend", {}).get("services", [])
        if backend_services:
            variables["backend_services"] = backend_services

        variables.update(secrets_vars)

        # Jinja2 环境
        env = Environment(
            loader=FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=Undefined,
        )

        generated = []

        def _render(template_rel: str, out_name: str, extra_vars: dict = None) -> str:
            """渲染单个模板并写入 config 目录"""
            tpl = env.get_template(template_rel)
            ctx = dict(variables)
            if extra_vars:
                ctx.update(extra_vars)
            content = tpl.render(**ctx)
            out_path = config_dir / out_name
            out_path.write_text(content, encoding="utf-8")
            generated.append(str(out_path))
            self._log(f"  生成: {out_name}")
            return str(out_path)

        # ── 1. 渲染 Docker Compose ──
        compose_file = preset_config.get("middleware", {}).get("compose_file")
        if compose_file:
            _render(f"compose/{compose_file}", "docker-compose.yaml")

        # ── 2. 渲染 .env ──
        _render("env/.env.j2", ".env")

        # ── 3. 渲染 Nginx 配置 ──
        arch_type = preset_config.get("architecture", {}).get("type", "spring-boot")
        if arch_type == "spring-cloud":
            # 微服务多路由 Nginx
            _render("nginx/spring-cloud.conf.j2", "nginx.conf")
        else:
            _render("nginx/app.conf.j2", "nginx.conf")

        # ── 4. 渲染 Application YAML ──
        services = preset_config.get("backend", {}).get("services", [])
        if services:
            # 多服务模式：每个服务独立 application.yaml + systemd
            for svc in services:
                svc_name = svc["name"]
                svc_port = svc.get("port", 8080)
                svc_vars = {
                    "app_name": svc_name,
                    "app_port": svc_port,
                    "service_name": svc_name,
                }
                _render("java/application.yaml.j2",
                        f"application-{svc_name}.yaml",
                        svc_vars)
                _render("systemd/spring-boot.service.j2",
                        f"systemd/{svc_name}.service",
                        svc_vars)
        else:
            # 单服务模式
            svc_name = preset_config.get("backend", {}).get("deploy", {}).get("service_name", "app")
            svc_port = variables.get("app_port", 8080)
            _render("java/application.yaml.j2", "application.yaml",
                     {"service_name": svc_name, "app_port": svc_port})
            _render("systemd/spring-boot.service.j2",
                    f"systemd/{svc_name}.service",
                    {"service_name": svc_name})

        self._log("配置文件准备完成")
        self._step("prepare_config", "completed",
                   f"生成 {len(generated)} 个配置文件")
        return generated

    def complete(self):
        """完成部署，生成清单"""
        self._manifest["status"] = "completed"

        manifest_path = self.workspace_dir / "deploy-manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(self._manifest, f, indent=2, ensure_ascii=False)

        self._log(f"部署清单: {manifest_path}")

    def fail(self, reason: str):
        """部署失败"""
        self._manifest["status"] = "failed"
        self._log(f"部署失败: {reason}")

        manifest_path = self.workspace_dir / "deploy-manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(self._manifest, f, indent=2, ensure_ascii=False)