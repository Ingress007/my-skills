#!/usr/bin/env python
"""app-deploy-ops CLI - 应用部署入口"""

import argparse
import sys
import os

# 添加项目根路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def cmd_init(args):
    """初始化环境"""
    from core.deployer import Deployer
    deployer = Deployer(args.env, args.server, args.preset)
    workspace_dir = deployer.init()

    print(f"\n✓ 工作空间初始化完成: {workspace_dir}")
    print("\n请填写环境配置:")
    print(f"  {os.path.expanduser(f'~/.app-deploy-ops/secrets/{args.env}/environment.yaml')}")
    print("    ├── 数据库: mysql.root_password, mysql.app_user, mysql.app_password, mysql.database")
    print("    ├── Redis:   redis.password")
    print("    ├── 应用:    app_port, log_level")
    print("    ├── 密钥:    jwt_secret, api_key")
    print("    └── ssl/    (可选证书)")
    print("\n完成后执行: python scripts/deploy.py deploy \\")
    print(f"  --server {args.server} --env {args.env} --preset {args.preset}")


def cmd_build(args):
    """本地构建应用"""
    from core.builder import NodeJSBuilder, MavenBuilder

    if args.type == "frontend":
        builder = NodeJSBuilder()

        if not builder.check_installed():
            print("Node.js 未安装。请先安装 Node.js 后再试。")
            sys.exit(1)

        workspace = os.path.expanduser(f"~/.app-deploy-ops/workspaces/{args.env}/current")
        if not os.path.exists(workspace):
            print("错误: 当前工作空间不存在，请先执行 init")
            sys.exit(1)

        output_dir = os.path.join(workspace, "artifacts", "dist")
        result = builder.build(args.source, output_dir)
        print(f"\n✓ 前端构建完成: {result['output']}")
        print(f"  产物数量: {result['files_count']} 个文件")

    elif args.type == "backend":
        builder = MavenBuilder()

        if not builder.check_installed():
            print("Maven 未安装。请先安装 Maven 后再试。")
            sys.exit(1)

        workspace = os.path.expanduser(f"~/.app-deploy-ops/workspaces/{args.env}/current")
        if not os.path.exists(workspace):
            print("错误: 当前工作空间不存在，请先执行 init")
            sys.exit(1)

        output_dir = os.path.join(workspace, "artifacts")
        result = builder.build(args.source, output_dir, args.profile)
        print(f"\n✓ 后端构建完成: {result['jar']}")
        print(f"  大小: {result['size']}")


def _get_services(preset_config: dict) -> list:
    """从预设中获取服务列表，兼容单服务和多服务"""
    services = preset_config.get("backend", {}).get("services", [])
    if not services:
        # 单服务模式
        svc_name = preset_config.get("backend", {}).get("deploy", {}).get("service_name", "app")
        svc_port = preset_config.get("variables", {}).get("app_port", 8080)
        services = [{"name": svc_name, "port": svc_port}]
    return services


def _deploy_services(args, preset_config: dict, deployer, ssh) -> list:
    """上传并部署后端服务（支持多服务）"""
    from remote.file_ops import FileManager
    from remote.systemd_ops import SystemdManager
    from core.backup import BackupManager
    from core.validator import Validator

    client = ssh.client
    fm = FileManager(client)
    backup = BackupManager(client, args.env)
    systemd = SystemdManager(client)
    validator = Validator()
    host = ssh.server_info.hostname

    services = _get_services(preset_config)
    deployed = []

    for svc in services:
        svc_name = svc["name"]
        svc_port = svc["port"]
        base_remote = f"{_app_base(args.env)}/backend/services/{svc_name}"

        deployer._log(f"── 部署服务 {svc_name} (端口 {svc_port}) ──")

        # 备份
        deployer._log(f"备份 {svc_name} ...")
        backup.backup_app(svc_name)

        # 上传 JAR
        jar_source = None
        if args.backend_dir:
            candidate = os.path.join(args.backend_dir, svc_name, "app.jar")
            if os.path.isfile(candidate):
                jar_source = candidate
        elif args.backend_jar and len(services) == 1:
            jar_source = args.backend_jar

        if jar_source:
            remote_jar = f"{base_remote}/app.jar"
            deployer._log(f"上传 JAR: {jar_source} -> {remote_jar}")
            fm.upload_file(jar_source, remote_jar)
        else:
            deployer._log(f"  跳过 JAR 上传（未提供 {svc_name} 的 JAR）")

        # 上传该服务的 application.yaml
        app_yaml_local = deployer.workspace_dir / "config" / f"application-{svc_name}.yaml"
        if app_yaml_local.exists():
            remote_yaml = f"{base_remote}/application.yaml"
            fm.upload_file(str(app_yaml_local), remote_yaml)

        # 上传该服务的 systemd service 文件
        svc_file_local = deployer.workspace_dir / "config" / "systemd" / f"{svc_name}.service"
        if svc_file_local.exists():
            remote_svc = f"/etc/systemd/system/{svc_name}.service"
            fm.upload_file(str(svc_file_local), remote_svc)

        # 重启服务
        deployer._log(f"重启 {svc_name} ...")
        result = systemd.restart(svc_name)
        deployer._log(f"  {svc_name} 重启结果: {result}")

        # 健康检查
        health = validator.check_health(host, svc_port)
        deployer._log(f"  {svc_name} 健康检查 (:{svc_port}): {health}")
        deployed.append({"name": svc_name, "port": svc_port, "health": health})

    return deployed


def _app_base(env: str) -> str:
    return f"/opt/apps/{env}"


def cmd_deploy(args):
    """执行部署"""
    from core.deployer import Deployer
    import yaml

    # 加载预设配置
    preset_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "presets", f"{args.preset}.yaml")
    if not os.path.exists(preset_path):
        print(f"错误: 预设配置不存在: {preset_path}")
        sys.exit(1)

    with open(preset_path, "r", encoding="utf-8") as f:
        preset_config = yaml.safe_load(f)

    deployer = Deployer(args.env, args.server, args.preset)

    # 1. 初始化
    deployer.init()

    # 2. 检查敏感配置
    if not deployer.check_secrets():
        print("\n请先填写敏感配置后再部署:")
        print(f"  ~/.app-deploy-ops/secrets/{args.env}/")
        deployer.fail("敏感配置未填写")
        sys.exit(1)

    # 3. 准备配置文件
    template_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "templates")
    deployer.prepare_config(preset_config, template_dir)

    # 4. 连接服务器
    from remote.ssh_ops import SSHManager
    ssh = SSHManager()
    try:
        client = ssh.connect(args.server)
        deployer._log(f"SSH 连接成功: {args.server}")

        # 5. 上传前端
        if args.frontend_dist:
            from remote.file_ops import FileManager
            fm = FileManager(client)
            remote_dist_path = f"{_app_base(args.env)}/frontend/vue-app/dist"
            deployer._log("上传前端构建产物...")
            fm.upload_dir(args.frontend_dist, remote_dist_path)

        # 6. 上传配置文件（共享配置，非 service 特定）
        from remote.file_ops import FileManager
        fm = FileManager(client)
        workspace_dir = deployer.workspace_dir
        config_dir = workspace_dir / "config"
        if config_dir.exists():
            for f in config_dir.iterdir():
                if f.is_file() and f.suffix in (".yaml", ".yml", ".conf", ".env"):
                    remote_path = f"{_app_base(args.env)}/config/{f.name}"
                    fm.upload_file(str(f), remote_path)

        # 7. 部署中间件
        if preset_config.get("middleware", {}).get("enabled", False):
            from remote.docker_ops import DockerManager
            docker = DockerManager(client)
            docker_info = docker.check_docker()
            if docker_info["installed"]:
                deployer._log("启动中间件容器...")
                # 上传 docker-compose.yaml + .env
                compose_local = config_dir / "docker-compose.yaml"
                dotenv_local = config_dir / ".env"
                if compose_local.exists():
                    fm.upload_file(str(compose_local),
                                   f"{_app_base(args.env)}/middleware/docker-compose.yaml")
                if dotenv_local.exists():
                    fm.upload_file(str(dotenv_local),
                                   f"{_app_base(args.env)}/middleware/.env")
                compose_dir = f"{_app_base(args.env)}/middleware"
                result = docker.compose_up(compose_dir)
                deployer._log(result)
            else:
                deployer._log("Docker 未安装，跳过中间件部署")

        # 8. 部署应用服务（单服务 / 多服务）
        services = _get_services(preset_config)
        if not args.backend_jar and not args.backend_dir:
            deployer._log("警告: 未提供后端 JAR（--backend-jar / --backend-dir），仅做配置部署")
        else:
            deployer._log(f"检测到 {len(services)} 个后端服务，开始部署...")
            from remote.systemd_ops import SystemdManager
            systemd = SystemdManager(client)
            systemd.daemon_reload()

        deployed = _deploy_services(args, preset_config, deployer, ssh)

        ssh.disconnect()

    except Exception as e:
        deployer.fail(str(e))
        print(f"\n✗ 部署失败: {e}")
        sys.exit(1)

    # 9. 完成
    deployer.complete()
    print(f"\n✓ 部署完成")
    if deployed:
        print("  已部署服务:")
        for d in deployed:
            status = "✓" if d["health"].get("healthy") else "✗"
            print(f"    {status} {d['name']} (:{d['port']})")


def cmd_rollback(args):
    """回滚部署（支持单服务/多服务）"""
    from core.deployer import Deployer
    from remote.ssh_ops import SSHManager

    deployer = Deployer(args.env, args.server, args.preset)
    deployer.init()
    deployer._log(f"回滚到版本: {args.version}")

    # 确定回滚的服务名称列表
    if args.service:
        services = [{"name": args.service}]
    else:
        # 从 preset 获取服务列表
        import yaml
        preset_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "presets", f"{args.preset}.yaml")
        if os.path.exists(preset_path):
            with open(preset_path, "r", encoding="utf-8") as f:
                preset_config = yaml.safe_load(f)
            svcs = preset_config.get("backend", {}).get("services", [])
            if svcs:
                services = [{"name": s["name"]} for s in svcs]
            else:
                svc_name = preset_config.get("backend", {}).get("deploy", {}).get("service_name", "app")
                services = [{"name": svc_name}]
        else:
            services = [{"name": "app"}]

    ssh = SSHManager()
    try:
        client = ssh.connect(args.server)

        all_ok = True
        for svc in services:
            svc_name = svc["name"]
            backup_file = f"/opt/apps/{args.env}/backup/app/{svc_name}.jar.{args.version}.bak"
            app_path = f"/opt/apps/{args.env}/backend/services/{svc_name}/app.jar"

            deployer._log(f"回滚 {svc_name} ...")
            stdin, stdout, stderr = client.exec_command(
                f"test -f {backup_file} && cp {backup_file} {app_path} && echo 'OK'")
            result = stdout.read().decode().strip()

            if "OK" in result:
                from remote.systemd_ops import SystemdManager
                systemd = SystemdManager(client)
                systemd.restart(svc_name)
                print(f"  ✓ {svc_name} 回滚完成: {args.version}")
            else:
                print(f"  ✗ {svc_name} 备份文件不存在: {backup_file}")
                all_ok = False

        ssh.disconnect()
        if all_ok:
            print(f"\n✓ 回滚完成: {args.version}")
        else:
            print(f"\n⚠ 部分回滚完成（部分服务因备份缺失跳过）")

    except Exception as e:
        print(f"\n✗ 回滚失败: {e}")
        sys.exit(1)


def cmd_status(args):
    """查看环境状态"""
    from remote.ssh_ops import SSHManager
    import yaml

    ssh = SSHManager()
    try:
        client = ssh.connect(args.server)

        print(f"环境: {args.env}")
        print(f"服务器: {args.server}")
        print()

        # 检查 Docker 状态
        from remote.docker_ops import DockerManager
        docker = DockerManager(client)
        docker_info = docker.check_docker()
        if docker_info["installed"]:
            print(f"Docker: v{docker_info['version']}")
            containers = docker.compose_ps(f"/opt/apps/{args.env}/middleware")
            print(f"容器数量: {len(containers)}")
            for c in containers:
                print(f"  {c}")
        else:
            print("Docker: 未安装")
        print()

        # 检查应用服务状态 - 支持多服务
        from remote.systemd_ops import SystemdManager
        systemd = SystemdManager(client)

        # 尝试获取预设中的服务列表
        preset_name = getattr(args, 'preset', 'spring-boot-vue')
        preset_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "presets", f"{preset_name}.yaml")
        if os.path.exists(preset_path):
            with open(preset_path, "r", encoding="utf-8") as f:
                preset_config = yaml.safe_load(f)
            services = preset_config.get("backend", {}).get("services", [])
            if not services:
                svc_name = preset_config.get("backend", {}).get("deploy", {}).get("service_name", "app")
                services = [{"name": svc_name}]
        else:
            services = [{"name": "app"}]

        print("应用服务:")
        for svc in services:
            svc_name = svc["name"]
            status = systemd.status(svc_name)
            print(f"  {svc_name}: {status['active']} (PID: {status['pid'] or 'N/A'})")
            print(f"    开机自启: {status['enabled']}")

        ssh.disconnect()
    except Exception as e:
        print(f"\n✗ 状态检查失败: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="app-deploy-ops - 应用部署工具")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # init
    p_init = subparsers.add_parser("init", help="初始化环境")
    p_init.add_argument("--server", required=True, help="SSH 服务器名")
    p_init.add_argument("--env", required=True, help="环境名称 (prod/staging/test)")
    p_init.add_argument("--preset", default="spring-boot-vue",
                        help="预设配置名")

    # build
    p_build = subparsers.add_parser("build", help="本地构建")
    p_build.add_argument("--env", required=True, help="环境名称")
    p_build.add_argument("--type", required=True,
                         choices=["frontend", "backend"],
                         help="构建类型")
    p_build.add_argument("--source", required=True, help="项目目录")
    p_build.add_argument("--profile", default=None, help="Maven profile")

    # deploy
    p_deploy = subparsers.add_parser("deploy", help="执行部署")
    p_deploy.add_argument("--server", required=True, help="SSH 服务器名")
    p_deploy.add_argument("--env", required=True, help="环境名称")
    p_deploy.add_argument("--preset", default="spring-boot-vue",
                          help="预设配置名")
    p_deploy.add_argument("--backend-jar", help="后端 JAR 包路径（单服务模式）")
    p_deploy.add_argument("--backend-dir", help="后端多服务 JAR 目录（子目录名=服务名，内含 app.jar）")
    p_deploy.add_argument("--frontend-dist", help="前端 dist 目录路径")

    # rollback
    p_rollback = subparsers.add_parser("rollback", help="回滚部署")
    p_rollback.add_argument("--server", required=True, help="SSH 服务器名")
    p_rollback.add_argument("--env", required=True, help="环境名称")
    p_rollback.add_argument("--preset", default="spring-boot-vue",
                            help="预设配置名")
    p_rollback.add_argument("--version", required=True, help="回滚到版本（备份时间戳）")
    p_rollback.add_argument("--service", default=None,
                            help="指定回滚的服务名（留空则回滚预设中所有服务）")

    # status
    p_status = subparsers.add_parser("status", help="查看状态")
    p_status.add_argument("--server", required=True, help="SSH 服务器名")
    p_status.add_argument("--env", required=True, help="环境名称")
    p_status.add_argument("--preset", default="spring-boot-vue",
                          help="预设配置名（用于读取服务列表）")

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return

    # 分发命令
    commands = {
        "init": cmd_init,
        "build": cmd_build,
        "deploy": cmd_deploy,
        "rollback": cmd_rollback,
        "status": cmd_status,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()