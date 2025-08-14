from __future__ import annotations

import asyncio
import threading
from collections.abc import AsyncIterator, Iterator
from queue import Queue

from openai import OpenAI

from utils.config import settings
from utils.logging import get_logger

logger = get_logger()


def _create_openai_client() -> OpenAI:
    """
    创建并返回 OpenAI 客户端。

    读取 `settings.OPENAI_API_KEY` 与 `settings.OPENAI_BASE_URL`。
    若缺少 API Key，将抛出异常，由上层捕获并转换为流状态错误。
    """

    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    client_kwargs = {"api_key": settings.OPENAI_API_KEY}
    if settings.OPENAI_BASE_URL:
        client_kwargs["base_url"] = settings.OPENAI_BASE_URL

    return OpenAI(**client_kwargs)


def _iter_openai_tokens(prompt: str) -> Iterator[str]:
    """
    同步迭代器：使用 OpenAI Chat Completions 流式接口，逐个产出内容增量。
    """

    client = _create_openai_client()
    model_name = settings.OPENAI_MODEL or "gpt-5-mini"

    logger.debug("starting OpenAI streaming (model=%s)", model_name)

    stream = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )

    for chunk in stream:
        # 兼容 OpenAI 以及同构兼容实现：从 delta.content 中取文本
        try:
            choices = getattr(chunk, "choices", None)
            if not choices:
                continue
            first_choice = choices[0]
            delta = getattr(first_choice, "delta", None)
            if not delta:
                continue
            content = getattr(delta, "content", None)
            if content:
                yield content
        except Exception as exc:  # 容错：单个分片解析失败时尽量不中断
            logger.warning("failed to parse streaming chunk: %r; raw=%r", exc, chunk)
            continue


async def openai_stream_iter(prompt: str) -> AsyncIterator[str]:
    """
    异步生成器：桥接同步 SDK 流式迭代为异步分片产出。

    - 后台线程负责从 OpenAI SDK 同步拉取分片并写入线程安全队列；
    - 前台以异步方式从队列读取并逐个 yield。
    - 如后台遇到异常，会将异常对象入队，前台读到后抛出，以便上层标记 ERROR。
    """

    queue: Queue[object] = Queue()

    def _producer() -> None:
        try:
            for token in _iter_openai_tokens(prompt):
                queue.put(token)
        except Exception as exc:  # 传递异常到异步消费者
            queue.put(exc)
        finally:
            queue.put(None)  # sentinel

    thread = threading.Thread(target=_producer, daemon=True)
    thread.start()

    while True:
        item = await asyncio.to_thread(queue.get)
        if item is None:  # type: ignore[comparison-overlap]
            break
        if isinstance(item, Exception):
            raise item
        yield item  # type: ignore[misc]
