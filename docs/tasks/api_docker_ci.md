## 任务：为 API 创建 Dockerfile 及仅构建镜像的 GitHub CI（不推送）

### 任务描述
为 `api` 模块提供容器化运行能力与自动化构建流程：
- 在 `api/` 目录下新增 `Dockerfile` 与启动脚本 `bin/boot.sh`（最小可行，仅运行 FastAPI，不包含数据库迁移）。
- 新增 GitHub Actions 工作流 `.github/workflows/only-build.yml`，对 API 目录变更进行 Docker 镜像构建验证（仅构建，不推送到任何仓库）。

### 任务目标（MVP → 完整版）
- MVP：
  - 可本地构建镜像并启动容器，`uvicorn` 启动 `api/app.py` 中的 `app`，默认监听 `0.0.0.0:8000`。默认一个 worker。
  - CI 在含 `api/**` 变更的分支提交时自动执行构建（`push: false`）。


### 参考与上下文
- 现有入口：`api/app.py` 暴露 `app`（FastAPI）。
- 依赖清单：`api/requirements.txt`。
- 可参考文档：`docs/tasks/llm_stream_reply.md` 的结构与“示例代码”呈现方式。

### 技术方案
- 基础镜像使用 `python:3.12-slim-bookworm`（或团队统一版本），镜像内工作目录设为 `/api`。
- 仅保留必要步骤：安装 Python 依赖、复制代码、以 `boot.sh` 启动 `uvicorn`。
- CI 使用 `docker/setup-buildx-action` 与 `docker/build-push-action`，通过 `dorny/paths-filter` 检测 `api/**` 变更后再构建。

#### 精简启动脚本 `api/bin/boot.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail

HOST=${HOST:-"0.0.0.0"}
PORT=${PORT:-8000}
WORKERS=${WORKERS:-1}
API_PATH=${API_PATH:-"/api"}

cd "$API_PATH"
echo "fastapi run on $HOST:$PORT with $WORKERS workers"
exec uvicorn app:app --host "$HOST" --port "$PORT" --workers "$WORKERS"
```

#### 精简 Dockerfile：`api/Dockerfile`
```dockerfile
FROM python:3.12-slim-bookworm

WORKDIR /api

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

RUN chmod +x /api/bin/boot.sh

EXPOSE 8000

ENTRYPOINT ["/api/bin/boot.sh"]
```

#### GitHub Actions（仅构建不推送）：`.github/workflows/only-build.yml`
```yaml
name: Only Build API

on:
  push:
    branches-ignore:
      - "main" # main分支执行附带推送的CI
  workflow_dispatch:

jobs:
  check-changes:
    runs-on: ubuntu-latest
    outputs:
      api-changed: ${{ steps.changes.outputs.api }}
    steps:
      - name: Checkout
        uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - name: Check for changes
        id: changes
        uses: dorny/paths-filter@v2
        with:
          base: main
          filters: |
            api:
              - 'api/**'

  api-build:
    runs-on: ubuntu-latest
    needs: check-changes
    steps:
      - name: Checkout
        uses: actions/checkout@v3

      - name: No API changes detected
        if: needs.check-changes.outputs.api-changed != 'true'
        run: |
          echo "🎯 No changes detected in API directory, skipping Docker image build"
          echo "📁 Scope checked: api/**"
          echo "✅ No build required, task completed"

      - name: Set up Docker Buildx
        if: needs.check-changes.outputs.api-changed == 'true'
        uses: docker/setup-buildx-action@v2
        with:
          driver-opts: |
            image=moby/buildkit:v0.12.0

      - name: Build API Docker image
        if: needs.check-changes.outputs.api-changed == 'true'
        uses: docker/build-push-action@v4
        with:
          context: api
          push: false
          file: api/Dockerfile
          tags: api:local
          platforms: linux/amd64

      - name: API build completed
        if: needs.check-changes.outputs.api-changed == 'true'
        run: |
          echo "🚀 API Docker image build completed"
          echo "📦 Image tag: api:local"
```

### 目录/文件变更
- `api/bin/boot.sh`
- `api/Dockerfile`
- `.github/workflows/only-build.yml`

### 任务步骤
1. 新增文件：`api/bin/boot.sh`、`api/Dockerfile`、`.github/workflows/only-build.yml`。
2. 本地验证：
   - 构建：`docker build -f api/Dockerfile -t api:local api`
   - 运行：`docker run --rm -p 8000:8000 api:local`
   - 访问：`http://localhost:8000/docs`
3. 推送分支，触发 CI：若仅 `api/**` 变更，则执行 Docker 构建并通过。

### 验收标准
- 本地镜像可成功构建并启动，FastAPI 可通过 `/docs` 访问。
- GitHub Actions 在 `api/**` 发生变更时成功完成“仅构建”流程（`push: false`）。

### 待讨论事项
- 是否需要多架构构建与缓存配置（`cache-from/cache-to`）以提升 CI 速度。
- 是否需要在受保护分支或手动触发时推送镜像（后续版本再启用）。
- 基础镜像版本与安全加固（非 root、只读文件系统等）是否纳入本次范围。

上面的待讨论事项暂时不考虑，先完成基础的构建和CI。

### 里程碑与产出
- M1：完成 `Dockerfile` 与 `boot.sh`（本地可运行）。
- M2：完成 CI 仅构建流程并在分支上验证通过。
- M3（可选）：构建缓存、多架构与推送策略。

### 当前进度概览
- 待办：按本文档新增文件并验证本地与 CI 构建。
