# Vue 3 前端测试项目

用于 `app-deploy-ops` 部署测试的 Vue 3 前端项目。

## 技术栈

| 技术 | 版本 |
|------|------|
| Vue | 3.x |
| Vite | ^8.0 |
| TypeScript | ~6.0 |
| Node.js | >=18 |

## 构建产物

- 构建命令: `npm run build` (tsc && vite build)
- 产物目录: `dist/`
- 部署方式: Nginx 静态资源托管

## 部署配置 (app-deploy-ops)

### 预设

使用 `spring-boot-vue` 或 `spring-cloud-vue` 预设，将本项目的 `dist/` 部署到 Nginx 静态目录。

### 构建命令

```bash
python scripts/deploy.py build \
  --env prod \
  --type frontend \
  --source /path/to/test-project/vue3-app
```

### 构建产物路径

```
~/.app-deploy-ops/workspaces/{env}/current/artifacts/dist/
├── index.html
├── assets/
│   ├── index-*.js
│   └── index-*.css
```

### 部署目标

| 配置项 | 预设值 | 说明 |
|--------|--------|------|
| 部署类型 | nginx-static | Nginx 托管前端静态文件 |
| 服务器路径 | `/opt/apps/{env}/frontend/vue-app/dist/` | 预设 `frontend.dist_dir` |
| Nginx 配置 | `app.conf.j2` | 代理 `/api/` 到后端 |

### Nginx 路由

- `/` → 前端静态资源 (SPA，`try_files $uri /index.html`)
- `/api/*` → 反向代理到后端
- 静态资源 (`js|css|png|svg`) → 7 天缓存

## 本地开发

```bash
npm install
npm run dev    # Vite 开发服务器
npm run build  # 生产构建
```