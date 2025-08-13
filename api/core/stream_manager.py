"""
流式会话管理（内存版，模拟流式产出）

- 单进程内存字典承载共享状态：
  state = { stream_id: {"status": "running|done|stopping|error:...", "content": str} }
- 优先在现有事件循环中使用 asyncio.create_task 启动 worker；
  若当前上下文无运行中的事件循环，则回退到后台线程内以 asyncio.run 执行。
"""

from __future__ import annotations

import asyncio
import threading
import time
import uuid
from collections.abc import AsyncIterator
from enum import Enum
from typing import Any

from utils.logging import get_logger

logger = get_logger()


class StreamStatus(Enum):
    RUNNING = "running"
    DONE = "done"
    STOPPING = "stopping"
    ERROR = "error"
    MISSING = "missing"


# 共享状态：{ stream_id: {"status": StreamStatus, "content": str, "error"?: str} }
_streams_state: dict[str, dict[str, Any]] = {}


def start_stream(prompt: str) -> str:
    """创建一个新的流式会话并在后台开始产出。

    优先使用同事件循环的 create_task；若无运行中的事件循环，回退到后台线程。

    Args:
        prompt: 用于驱动模拟流的提示词（在模拟阶段仅用于回显）

    Returns:
        生成的 stream_id
    """
    stream_id = uuid.uuid4().hex
    _streams_state[stream_id] = {"status": StreamStatus.RUNNING, "content": ""}

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # 当前上下文没有运行中的事件循环：回退到线程 + asyncio.run
        logger.warning("没有检测到运行中的事件循环，回退到后台线程执行流式任务 (stream_id: %s)", stream_id)
        thread = threading.Thread(
            target=lambda: asyncio.run(_worker(stream_id=stream_id, prompt=prompt)),
            daemon=True,
        )
        thread.start()
    else:
        # 在已有事件循环中，直接调度后台任务
        loop.create_task(_worker(stream_id=stream_id, prompt=prompt))

    return stream_id


def get_stream_state(stream_id: str) -> dict:
    """查询指定流的当前状态（对外直接返回枚举）。"""
    state = _streams_state.get(stream_id)
    if state is None:
        return {"status": StreamStatus.MISSING, "content": ""}

    result = {"status": state.get("status", StreamStatus.MISSING), "content": state.get("content", "")}
    if result["status"] == StreamStatus.ERROR and "error" in state:
        result["error"] = state["error"]
    return result


def stop_stream(stream_id: str) -> None:
    """请求停止指定流的产出。"""
    if stream_id in _streams_state:
        _streams_state[stream_id]["status"] = StreamStatus.STOPPING


async def _mock_stream_iter(prompt: str) -> AsyncIterator[str]:
    """模拟流式分片产出：回显 prompt 并追加若干 token。"""
    # 尽量让单测更快：更短的 sleep
    tokens = [f"Q: {prompt}", "\n", "Hello", " ", "world", "!", " ", "This ", "is ", "a ", "stream."]
    for token in tokens:
        await asyncio.sleep(0.5)
        yield token


async def _worker(stream_id: str, prompt: str) -> None:
    """后台 worker：消费分片并累加到共享状态。"""
    try:
        async for chunk in _mock_stream_iter(prompt):
            # 若被请求停止，则提前退出
            if _streams_state.get(stream_id, {}).get("status") == StreamStatus.STOPPING:
                break
            # 累加分片
            if stream_id in _streams_state:
                _streams_state[stream_id]["content"] += chunk
        # 正常结束（未被删除）
        if stream_id in _streams_state and _streams_state[stream_id]["status"] == StreamStatus.RUNNING:
            # 若先前被标记为 stopping，这里不覆盖为 done，保持 stopping 以便上层识别
            _streams_state[stream_id]["status"] = StreamStatus.DONE
    except Exception as exc:  # pragma: no cover - 异常路径难以稳定复现
        if stream_id in _streams_state:
            _streams_state[stream_id]["status"] = StreamStatus.ERROR
            _streams_state[stream_id]["error"] = repr(exc)


# 简单轮询示例（便于本地临时验证）
if __name__ == "__main__":  # pragma: no cover
    sid = start_stream("示例问题：今天天气如何？")
    last = ""
    while True:
        state = get_stream_state(sid)
        if state["content"] != last:
            print("[poll]", state["content"])  # 观察增量
            last = state["content"]
        if state["status"] in (StreamStatus.ERROR, StreamStatus.DONE, StreamStatus.MISSING):
            print("[final]", state["content"])  # 最终内容
            break
        time.sleep(1)
