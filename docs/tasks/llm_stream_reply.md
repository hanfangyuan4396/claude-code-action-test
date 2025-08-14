## 任务：实现流式回复机器人（模拟 → 真实 LLM → 测试）

### 任务描述
基于企业微信“流式消息刷新”协议（见 `docs/wecom/接收消息.md`），实现一个可在后台产生并逐步输出内容的流式回复能力：
1) 首先实现模拟流式数据的回复通道（不依赖 LLM 接口）。
2) 随后集成真实 LLM 接口，复用相同流式通道协议。
3) 最后补充单元测试与集成测试。

### 任务目标（MVP → 完整版）
- MVP：提供一个内存级共享状态 `dict`，结构为 `{"stream_id": {"status": StreamStatus, "content": str, "error"?: str}}`，支持：
  - 生成 `stream_id`，后台异步产出分片内容，按序累加到 `content`；
  - 实时查询当前 `content` 和 `status`（使用枚举：RUNNING/DONE/STOPPING/ERROR/MISSING；错误详情通过 `error` 字段提供）。
  - 具备停止机制（可选）。
- 完整版：
  - 替换分片来源为真实 LLM 流（如 OpenAI/通义/Qwen 等），适配令牌续写。
  - 提供企业微信回调场景的对接点：当收到 `msgtype=stream` 的回调时，按 `stream.id` 返回流式分片（或在完成时一次性返回 `finish=true` 的最终结果）。
  - 覆盖单元与集成测试，确保核心行为稳定。

### 参考与上下文
- 企业微信协议：`docs/wecom/接收消息.md` 的“流式消息刷新”章节给出 `msgtype=stream` 与 `stream.id` 字段的语义。
- 现有回调服务样例：`api/service/wecom_callback_service.py` 中的 `process_callback_message` 展示了加解密与一个简化“流式消息”回复示例（当前为一次性 `finish=true`）。

### 技术方案
- 并发模型：
  - 采用 `threading.Thread` 启动 `asyncio.run` 执行异步生产，避免阻塞主线程；
  - 共享状态以单进程内存 `dict` 承载，键为 `stream_id`（暂不考虑多进程/多副本）。
- 共享状态结构：
  - `state = { stream_id: {"status": StreamStatus, "content": "", "error"?: str} }`
- 模拟流式阶段：
  - 使用内置异步迭代器按 token 片段产出（每次 sleep 模拟延迟）。
  - 后台 worker 将分片累加到 `content`，并在完成时标为 `done`。
- 真实 LLM 集成（仅 OpenAI SDK）：
  - 直接在 worker 中调用 OpenAI 流式接口产出分片，不引入多 provider 抽象；
  - 后续如需扩展其它 provider，再进行抽象与重构。
- API/回调对接：
  - 服务模块 `api/core/stream_manager.py` 统一管理 `start_stream(prompt) -> stream_id`、`get_stream_state(stream_id)` 与 `stop_stream(stream_id)`；
  - 在企业微信回调处理中：
    - 收到 `msgtype=stream` 且附带 `stream.id` 时，根据当前内容将分片返回；
    - 若业务需 push 模式，可在完成时返回 `finish=true` 的最终结果（示例已有）。
- 错误与停止：
  - worker 捕获异常时将 `status=StreamStatus.ERROR`，并写入 `error=repr(e)`；
  - 支持 `status==StreamStatus.STOPPING` 中断生产。

#### 示例代码（模拟流式最小可行 demo，使用枚举）
```python
import asyncio
import threading
import time
import uuid
from enum import Enum
from typing import Any, AsyncIterator

class StreamStatus(Enum):
    RUNNING = "running"
    DONE = "done"
    STOPPING = "stopping"
    ERROR = "error"
    MISSING = "missing"

state: dict[str, dict[str, Any]] = {"streams": {}}  # { stream_id: {"status": StreamStatus, "content": str, "error"?: str} }

def start_stream(prompt: str) -> str:
    stream_id = uuid.uuid4().hex
    state["streams"][stream_id] = {"status": StreamStatus.RUNNING, "content": ""}
    t = threading.Thread(target=lambda: asyncio.run(_worker(stream_id, prompt)), daemon=True)
    t.start()
    return stream_id

async def _mock_stream_iter(prompt: str) -> AsyncIterator[str]:
    # 仅为演示：将 prompt 回显并追加若干 token
    tokens = [f"Q: {prompt}", "\n", "Hello", " ", "world", "!", " ", "This ", "is ", "a ", "stream."]
    for token in tokens:
        await asyncio.sleep(0.5)
        yield token

async def _worker(stream_id: str, prompt: str):
    try:
        async for chunk in _mock_stream_iter(prompt):
            if state["streams"].get(stream_id, {}).get("status") == StreamStatus.STOPPING:
                break
            state["streams"][stream_id]["content"] += chunk
        # 若正常结束且未被中断
        if state["streams"].get(stream_id):
            state["streams"][stream_id]["status"] = StreamStatus.DONE
    except Exception as e:
        if state["streams"].get(stream_id) is not None:
            state["streams"][stream_id]["status"] = StreamStatus.ERROR
            state["streams"][stream_id]["error"] = repr(e)

def get_stream_state(stream_id: str) -> dict:
    s = state["streams"].get(stream_id)
    if not s:
        return {"status": StreamStatus.MISSING, "content": ""}
    result = {"status": s["status"], "content": s.get("content", "")}
    if result["status"] == StreamStatus.ERROR and "error" in s:
        result["error"] = s["error"]
    return result

def stop_stream(stream_id: str) -> None:
    if stream_id in state["streams"]:
        state["streams"][stream_id]["status"] = StreamStatus.STOPPING

# 简单轮询示例
if __name__ == "__main__":
    sid = start_stream("示例问题：今天天气如何？")
    last = ""
    while True:
        s = get_stream_state(sid)
        if s["content"] != last:
            print("[poll]", s["content"])  # 观察增量
            last = s["content"]
        if s["status"] in (StreamStatus.ERROR, StreamStatus.DONE, StreamStatus.MISSING):
            print("[final]", s["content"])  # 最终内容
            break
        time.sleep(0.5)
```

#### OpenAI SDK 流式集成示例（后续替换上方 _mock_stream_iter）
```python
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def _openai_stream_iter(prompt: str):
    # 使用 Chat Completions 流式接口
    stream = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )
    for chunk in stream:
        delta = getattr(chunk.choices[0], "delta", None)
        if delta and getattr(delta, "content", None):
            yield delta.content
```

### 目录/文件变更（已更新）
- `api/core/stream_manager.py`：共享状态与 worker 的统一管理，并暴露接口：
  - `start_stream(prompt: str) -> str`
  - `get_stream_state(stream_id: str) -> dict`（返回 `StreamStatus`）
  - `stop_stream(stream_id: str) -> None`
- 测试：
  - `tests/unit/test_stream_manager.py`
  - `tests/integration/test_wecom_stream_flow.py`

### 待讨论事项
- 仅使用 OpenAI SDK；如后续需多 provider，再进行抽象与扩展。
- 企业微信侧拉取式 vs 推送式的流式刷新细节与频率限制。
- `content` 是否需要附加增量游标，便于客户端只取差量。
- 暂不考虑多进程/多副本（后续可迁移到 Redis 统一状态）。

### 任务步骤
1. 模拟流式能力（MVP）
   - 在 `stream_manager` 中实现后台 worker 与 `_mock_stream_iter`；
   - 支持创建、查询、停止；
   - 提供最小 API 或 CLI 用例验证流式累加。
2. 接入真实 LLM（OpenAI SDK）
   - 在 `stream_manager` 中增加 `_openai_stream_iter`，以配置开关从模拟切换为 OpenAI；
   - 参数管理（密钥、超时、重试、最大 token 等）。
3. 企业微信回调对接
   - 在回调处理处接入 `stream_manager`；
   - 完成一次性完成响应与按需增量返回的两种形式（至少保证一种）。
4. 测试
   - 单元测试：以模拟流驱动，覆盖创建、增量、完成、异常、停止；
   - 集成测试：模拟 wecom 回调流程，验证 `stream.id` 与内容刷新；
5. 文档与示例
   - 在 `README.md` 或 `docs/tests/` 增补运行说明与示例脚本。

### 验收标准
- 提供可运行示例，展示从 `start_stream` 到 `done` 的完整生命周期，轮询能看到 `content` 增长。
- 接入 OpenAI 后，通过配置开关即可从模拟切换为真实流式，不改变上层接口。
- 单元与集成测试均通过。

### 里程碑与产出
- M1：模拟流式功能落地（已完成）
  - 内存版流管理器：`api/core/stream_manager.py`
  - 状态改为枚举 `StreamStatus`，对内对外统一
  - 单元测试通过（11 tests）
- M2：真实 LLM 接入（进行中/待办）
  - 计划接入 OpenAI 流式接口，替换 `_mock_stream_iter`
- M3：企业微信回调集成与集成测试（部分完成/待办）
  - 已在 `api/service/wecom_callback_service.py` 集成拉取式刷新（`msgtype=stream`）
  - 待补充端到端集成测试

### 当前进度概览
- 已完成：
  - `stream_manager` 迁移至 `core` 层，并公开 `StreamStatus` 枚举
  - 业务与测试均改为依赖枚举（不再比较字符串）
  - 企业微信回调对接拉取式刷新逻辑（基于枚举完成态 DONE/ERROR）
  - 全部单测通过（11/11）
- 待办：
  - 接入真实 LLM Provider（OpenAI 优先），完善超时/重试/限流
  - 增补集成测试与 README 操作指引（端到端）
  - 如需支持多进程/多副本，迁移共享状态至 Redis

### 使用说明（OpenAI 流式开关）
- 在 `api/.env.example` 中复制为 `api/.env` 并填写：
  - `OPENAI_API_KEY`
  - 可选：`OPENAI_BASE_URL`（代理或自建网关时）
  - 可选：`OPENAI_MODEL`（默认 `gpt-5-mini`）
- 安装依赖：
  - `/home/hfy/miniconda3/envs/claude-test/bin/python -m pip install -r api/requirements.txt`
- 运行服务或本地验证脚本时，若检测到 `OPENAI_API_KEY`，`stream_manager` 将自动切换为真实 LLM 流式；否则使用模拟流。
