import time

import pytest

from core.stream_manager import StreamStatus, get_stream_state, start_stream, stop_stream


def test_stream_lifecycle_accumulates_and_finishes():
    stream_id = start_stream("hello")

    # 轮询等待内容增长与完成
    last = ""
    deadline = time.time() + 10
    saw_growth = False
    while time.time() < deadline:
        state = get_stream_state(stream_id)
        if state["content"] != last and state["content"]:
            saw_growth = True
            last = state["content"]
        if state["status"] == StreamStatus.DONE:
            break
        time.sleep(0.5)

    # 若因超时而退出循环，提供更清晰的诊断信息
    now_after_loop = time.time()
    final_state = get_stream_state(stream_id)
    if now_after_loop >= deadline and final_state["status"] != StreamStatus.DONE:
        raise AssertionError(
            f"Stream {stream_id} polling timed out before DONE. "
            f"saw_growth={saw_growth}, final_status={final_state['status']}, "
            f"final_content={final_state['content']!r}"
        )
    assert saw_growth is True
    assert final_state["status"] == StreamStatus.DONE
    assert "stream." in final_state["content"]


def test_stream_can_be_stopped():
    stream_id = start_stream("to stop")

    # 等到有点内容后停止
    wait_seconds = 5
    deadline = time.time() + wait_seconds
    saw_content = False
    while time.time() < deadline:
        state = get_stream_state(stream_id)
        if state["content"]:
            saw_content = True
            break
        time.sleep(0.5)

    # 超时后显式失败，避免测试在未出现内容时继续或通过
    if not saw_content:
        final_state = get_stream_state(stream_id)
        pytest.fail(
            f"Stream {stream_id} timed out waiting for initial content; "
            f"no content appeared within {wait_seconds}s. "
            f"final_status={final_state['status']}, "
            f"final_content={final_state['content']!r}"
        )

    stop_stream(stream_id)

    # 停止后不强求 done，但应保持 stopping 或 done，且内容不会清空
    time.sleep(0.2)
    state_after = get_stream_state(stream_id)
    assert state_after["status"] in (StreamStatus.STOPPING, StreamStatus.DONE)
    assert isinstance(state_after["content"], str)
