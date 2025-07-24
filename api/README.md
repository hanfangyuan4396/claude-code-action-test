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