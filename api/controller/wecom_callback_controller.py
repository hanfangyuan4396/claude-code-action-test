"""
企业微信回调控制器
负责处理企业微信回调相关的HTTP请求和响应，只做协议适配和参数校验，调用service层处理业务逻辑
"""

from typing import Annotated

from fastapi import APIRouter, Body, Query, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from service.wecom_callback_service import WeComService
from utils.config import settings
from utils.logging import get_logger

logger = get_logger()
router = APIRouter()


@router.get("/wecom/callback")
async def wecom_callback_get(
    msg_signature: str | None = Query(default=None),
    timestamp: str | None = Query(default=None),
    nonce: str | None = Query(default=None),
    echostr: str | None = Query(default=None),
) -> PlainTextResponse:
    """企业微信服务器验证URL有效性

    重构后实现：
    - 使用WeComService处理业务逻辑
    - 控制器层仅负责协议适配和参数校验
    - 保持原有的请求/响应格式和状态码
    """

    logger.debug(
        "wecom_callback params: msg_signature=%s timestamp=%s nonce=%s echostr=%s",
        msg_signature,
        timestamp,
        nonce,
        echostr,
    )

    # 初始化WeComService（配置完整性已在启动时校验）
    wecom_service = WeComService(
        token=settings.WECOM_TOKEN, encoding_aes_key=settings.WECOM_ENCODING_AES_KEY, corp_id=settings.WECOM_CORP_ID
    )

    # 验证参数完整性
    params_valid, params_error = wecom_service.validate_callback_params(
        msg_signature=msg_signature, timestamp=timestamp, nonce=nonce, echostr=echostr
    )
    if not params_valid:
        return PlainTextResponse("missing required query params", status_code=400)

    # 处理URL验证
    success, result = wecom_service.verify_callback_url(
        msg_signature=msg_signature, timestamp=timestamp, nonce=nonce, echostr=echostr
    )

    if success:
        return PlainTextResponse(result)
    elif result == "invalid signature":
        return PlainTextResponse("invalid signature", status_code=400)
    else:
        return PlainTextResponse("internal error", status_code=500)


@router.post("/wecom/callback")
async def wecom_callback_post(
    request: Request,
    body: Annotated[dict, Body(...)],
    msg_signature: str = Query(..., description="企业微信签名 msg_signature"),
    timestamp: str = Query(..., description="时间戳 timestamp（字符串）"),
    nonce: str = Query(..., description="随机串 nonce"),
):
    """企业微信回调消息处理（POST）

    重构后实现：
    - 使用WeComService处理业务逻辑
    - 控制器层仅负责协议适配和参数校验
    - 保持原有的请求/响应格式和状态码
    """
    # 读取 JSON 请求体并直接取 encrypt（签名中声明为 dict，无需再判断类型）
    encrypt = body.get("encrypt")
    if not isinstance(encrypt, str) or not encrypt:
        return PlainTextResponse("missing encrypt in body", status_code=400)

    # 初始化WeComService（配置完整性已在启动时校验）
    wecom_service = WeComService(
        token=settings.WECOM_TOKEN, encoding_aes_key=settings.WECOM_ENCODING_AES_KEY, corp_id=settings.WECOM_CORP_ID
    )

    # 处理回调消息
    success, result, encrypted_response = wecom_service.process_callback_message(
        msg_signature=msg_signature, timestamp=timestamp, nonce=nonce, encrypt=encrypt
    )

    if success:
        return JSONResponse(content=encrypted_response)
    elif result == "invalid signature":
        return PlainTextResponse("invalid signature", status_code=400)
    else:
        return PlainTextResponse("internal error", status_code=500)
