# FastAPI Demo API

一个简单的 FastAPI 应用程序，用于演示基本的 Web API 功能。

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行应用

#### 方法1：直接运行Python文件
```bash
python app.py
```

#### 方法2：使用uvicorn命令
```bash
uvicorn app:app --reload
```

应用将在 `http://localhost:8000` 启动。

### API 端点

- `GET /` - 返回欢迎消息
- `GET /health` - 健康检查端点
- `GET /hello/{name}` - 个性化问候

### 交互式文档

启动应用后，可以访问：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 开发

使用 `--reload` 参数可以在代码更改时自动重启服务器。

### 运行测试（简要）

本项目使用 `pytest` 进行测试，测试代码位于 `api/tests/`。本地快速运行：

```bash
pip install -r requirements.txt
pytest -q --cov=core --cov-report=term-missing
```

CI 将在 Pull Request 上使用 Python 3.12 运行上述测试并输出覆盖率摘要（无外部依赖，如 Redis/MySQL）。

### Ruff 使用（代码规范与格式化）

建议在 `api/` 目录执行以下命令。

安装（一次性）：

```bash
pip install --upgrade ruff==0.12.8
```

检查（仅报告问题）：

```bash
ruff check .
```

自动修复并格式化：

```bash
ruff check . --fix && ruff format .
```

仅格式化：

```bash
ruff format .
```

### pre-commit（仅作用于 `api/`）

若未安装 pre-commit，请先：

```bash
pip install pre-commit==4.3.0
```

安装 Git 钩子（Ruff 钩子仅作用于 `api/`；空白修复钩子作用于全仓库）：

```bash
pre-commit install
```

对全仓库运行一遍钩子：

```bash
pre-commit run --all-files
```
