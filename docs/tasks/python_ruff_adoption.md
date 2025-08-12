# 在 Python 代码库引入 Ruff（格式化与静态检查）

## 任务描述

为本仓库的 Python 代码（主要位于 `api/` 目录）引入 Ruff，统一代码风格并在提交与 CI 环节中进行快速、可扩展的静态检查与自动格式化，降低代码审查与合并成本。

## 任务目标（Must）

- 统一 Python 代码风格，提供确定性的自动格式化能力
- 建立本地一致性（pre-commit）与远端一致性（CI）
- 首次批量修复后使 `ruff check` 和 `ruff format --check` 在 CI 通过
- 将使用说明写入 `README.md`（开发者能一键上手）

## 技术方案（可落地）

### 1) 工具选型

- 使用 Ruff 同时承担 linter 与 formatter 两个角色：
  - 代码风格与静态检查：`ruff check`
  - 代码格式化：`ruff format`
- 以 Ruff 替代传统的 flake8/isort/black 组合，减少工具碎片化与配置复杂度。

### 2) 配置与约定

- 使用根目录的 `.ruff.toml` 管理 Ruff 配置（不引入 `pyproject.toml`）。
- 采用最小必要配置，行宽 120，统一双引号，目标版本 Python 3.12。

```toml
line-length = 120
target-version = "py312"
src = ["api"]
exclude = [
  ".git",
  ".venv",
  "venv",
  "build",
  "dist",
  "docs",
  "__pycache__/*",
  "migrations/*",
]

[format]
line-ending = "lf"
quote-style = "double"

[lint]
# 最小必要规则集（易于落地，后续可按需增强）
select = [
  "E",   # pycodestyle
  "F",   # pyflakes
  "I",   # 导入排序
  "UP",  # 语法升级建议
  "B",   # bugbear
  "SIM", # 简化建议
  "RUF", # ruff 自身规则
]

[lint.per-file-ignores]
# app 入口存在延迟导入
"api/app.py" = ["E402"]
# 测试中允许 assert 与 fixture 重定义
"api/tests/*" = ["S101", "F811"]
```

说明：
- 相比你在 Flask 项目中的完整配置，这里去掉了与本仓库结构无关的分组（如 `models/`、`extensions/` 等），保留了 `app.py` 与 `tests/` 的必要定制。
- 安全规则按“最小可用集”启用，避免初期噪音；后续可增补（如 `S506` 等）。
- 若后期发现测试中存在更多风格特例，可在 `api/tests/*` 追加精确豁免，而非全局忽略。

### 3) 依赖与安装

- 开发者本地直接安装：

```bash
pip install --upgrade ruff==0.12.8
```

- 可选：新增 `api/requirements-dev.txt` 统一管理开发依赖（示例）：

```text
-r requirements.txt
ruff==0.12.8
pre-commit==4.3.0
```

### 4) 本地提交钩子（pre-commit）

- 在仓库根新增 `.pre-commit-config.yaml`：

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    # 通过 additional_dependencies 固定 ruff 版本
    rev: v0.6.9
    hooks:
      - id: ruff
        args: ["--fix"]
        additional_dependencies: ["ruff==0.12.8"]
        files: ^api/
      - id: ruff-format
        additional_dependencies: ["ruff==0.12.8"]
        files: ^api/

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: end-of-file-fixer
      - id: trailing-whitespace
```

说明：使用远程钩子仓库，首次会拉取并缓存钩子环境；通过 `rev` 和 `additional_dependencies` 保证版本可复现。Ruff 钩子仅作用于 `api/`；基础空白修复钩子（end-of-file-fixer、trailing-whitespace）作用于全仓库文本文件。

- 启用：

```bash
pip install pre-commit==4.3.0 && pre-commit install
```

### 5) CI 集成（GitHub Actions）

- 新增工作流 `.github/workflows/python-lint.yml`：

```yaml
name: Python Lint

on:
  pull_request:
  push:
    branches: [ main ]

jobs:
  ruff:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install ruff==0.12.8
      - run: ruff check .
      - run: ruff format --check .
```

说明：CI 仅做检查（不自动修改），保证 PR 必须满足规范；本地通过 pre-commit 自动修复。

### 6) 迁移策略

1. 试运行（不修改）：`ruff check . --statistics`
2. 一次性自动修复：`ruff check . --fix && ruff format .`
3. 对少量无法自动修复的问题，逐个手动处理；必要时在 `ignore` 或 `per-file-ignores` 中添加临时豁免
4. 切分提交：将“纯格式化改动”独立提交，降低代码审查成本
5. 当 CI 全绿后，将本任务标记完成

### 7) 目录范围与排除

- 默认对 `api/` 生效；排除 `docs/`、虚拟环境、构建产物等非源码目录
- 如测试目录短期内误报较多，可针对 `api/tests/` 设置 `per-file-ignores` 逐步收敛

## 待讨论事项

- 是否在首轮启用更多规则（如 `N`、`PT`、`C4`、`S*`、`TRY*` 等）
- 是否在 CI 中引入缓存（加速 `pip` 和 Ruff 执行）
- 是否创建并维护 `api/requirements-dev.txt`

## 任务步骤

1. 在根目录新增 `.ruff.toml`（Ruff 配置）
2. 新增 `.pre-commit-config.yaml` 并执行 `pre-commit install`
3. 可选：新增 CI 工作流 `.github/workflows/python-lint.yml`
4. 本地执行首次批量修复并分离提交
5. 在 `README.md` 补充开发说明与常用命令

### 可选增强规则候选清单（后续按需启用）

- 命名/可读性/复用：`PLR0402`, `PLR1711`, `PLR1714`
- PyLint 兼容类错误：`PLC0208`, `PLC0414`, `PLE0604`, `PLE0605`
- Refurb 建议：`FURB` 全集（如 `FURB113`, `FURB152`）
-  Ruff 规则补充：`RUF013`, `RUF019`, `RUF022`, `RUF100`, `RUF101`, `RUF200`
- Try/异常风格：`TRY400`, `TRY401`
- 安全补充：`S506`（YAML load）, 以及更多 `S*` 规则
- Pycodestyle 补充：`W*`（如 `W605`），如需

## 里程碑与产出

- [ ] 配置文件落地：`.ruff.toml`、`.pre-commit-config.yaml`
- [ ] CI 工作流生效并通过首个 PR 检查
- [ ] 首次批量修复合并，CI 全绿
- [ ] `README.md` 更新完成

## 状态

- 状态：待开始
- 负责人：待指派
- 目标完成时间：待确定
