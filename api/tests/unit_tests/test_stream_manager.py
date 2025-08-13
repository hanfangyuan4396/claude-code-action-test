import time

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

    final_state = get_stream_state(stream_id)
    assert saw_growth is True
    assert final_state["status"] == StreamStatus.DONE
    assert "stream." in final_state["content"]


def test_stream_can_be_stopped():
    stream_id = start_stream("to stop")

    # 等到有点内容后停止
    deadline = time.time() + 5
    while time.time() < deadline:
        state = get_stream_state(stream_id)
        if state["content"]:
            break
        time.sleep(0.5)

    stop_stream(stream_id)

    # 停止后不强求 done，但应保持 stopping 或 done，且内容不会清空
    time.sleep(0.2)
    state_after = get_stream_state(stream_id)
    assert state_after["status"] in (StreamStatus.STOPPING, StreamStatus.DONE)
    assert isinstance(state_after["content"], str)
