from typing import Any

from fastapi import APIRouter, Request

from service.echo_service import EchoService

router = APIRouter()


@router.get("/echo")
async def echo_get(request: Request) -> dict[str, Any]:
    headers = dict(request.headers)
    query_params = dict(request.query_params)
    echo_service = EchoService()
    return echo_service.build_echo_get_response(
        method=request.method,
        url=str(request.url),
        headers=headers,
        query_params=query_params,
    )


@router.post("/echo")
async def echo_post(request: Request) -> dict[str, Any]:
    headers = dict(request.headers)
    query_params = dict(request.query_params)
    try:
        body_bytes = await request.body()
        body_text = body_bytes.decode("utf-8", errors="ignore") if body_bytes else ""
    except Exception:
        body_text = ""

    echo_service = EchoService()
    return echo_service.build_echo_post_response(
        method=request.method,
        url=str(request.url),
        headers=headers,
        query_params=query_params,
        body_text=body_text,
    )
