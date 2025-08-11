from fastapi import APIRouter, Request
from typing import Dict, Any
from service.echo_service import EchoService
from utils.logging import get_logger


router = APIRouter()
logger = get_logger()


@router.get("/echo")
async def echo_get(request: Request) -> Dict[str, Any]:
    headers = dict(request.headers)
    query_params = dict(request.query_params)
    logger.info(
        "method=%s url=%s headers=%s query=%s",
        request.method,
        str(request.url),
        headers,
        query_params,
    )
    echo_service = EchoService()
    return echo_service.build_echo_get_response(headers=headers, query_params=query_params)
