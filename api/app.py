from fastapi import FastAPI, Request, Query, Body
from fastapi.responses import PlainTextResponse, JSONResponse
import xml.etree.ElementTree as ET
from wecom.verify import WeComURLVerifier
from wecom import WeComMessageCrypto
from wechatpy.exceptions import InvalidSignatureException
import os
import uvicorn
import logging
from typing import Annotated
from pathlib import Path
from dotenv import load_dotenv
import json

app = FastAPI(
    title="FastAPI Demo",
    description="A simple FastAPI application",
    version="1.0.0"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("app.request")

# 加载本地 .env 文件（位于与本文件同目录的 `.env`）
load_dotenv(dotenv_path=Path(__file__).with_name(".env"))

# 读取环境变量
WECOM_TOKEN = os.getenv("WECOM_TOKEN")
WECOM_ENCODING_AES_KEY = os.getenv("WECOM_ENCODING_AES_KEY")
WECOM_CORP_ID = os.getenv("WECOM_CORP_ID", "")
logger.info(f"token: {WECOM_TOKEN} encoding_aes_key: {WECOM_ENCODING_AES_KEY} corp_id: {WECOM_CORP_ID}")

@app.get("/echo")
async def echo_get(request: Request):
    headers = dict(request.headers)
    query_params = dict(request.query_params)
    logger.info(
        "method=%s url=%s headers=%s query=%s",
        request.method,
        str(request.url),
        headers,
        query_params,
    )
    return {
        "method": "GET",
        "headers": headers,
        "query": query_params,
    }

@app.post("/echo")
async def echo_post(request: Request):
    headers = dict(request.headers)
    query_params = dict(request.query_params)

    try:
        body_bytes = await request.body()
        body_text = body_bytes.decode("utf-8", errors="ignore") if body_bytes else ""
    except Exception:
        body_text = ""

    logger.info(
        "method=%s url=%s headers=%s query=%s body=%s",
        request.method,
        str(request.url),
        headers,
        query_params,
        body_text,
    )

    return {
        "method": "POST",
        "headers": headers,
        "query": query_params,
        "body": body_text,
    }


@app.get("/wecom/callback")
async def wecom_callback_get(
    msg_signature: str | None = Query(default=None),
    timestamp: str | None = Query(default=None),
    nonce: str | None = Query(default=None),
    echostr: str | None = Query(default=None),
):
    """企业微信服务器验证URL有效性

    当前实现：
    - 记录请求参数
    - 从环境变量读取 Token/EncodingAESKey/CorpID
    - 使用 WeComURLVerifier 验证签名并解密 echostr
    - 验证成功返回明文 echostr，失败返回 400
    """

    logger.info(
        "wecom_callback params: msg_signature=%s timestamp=%s nonce=%s echostr=%s",
        msg_signature,
        timestamp,
        nonce,
        echostr,
    )

    # 参数校验
    if not all([msg_signature, timestamp, nonce, echostr]):
        return PlainTextResponse("missing required query params", status_code=400)


    if not WECOM_TOKEN or not WECOM_ENCODING_AES_KEY:
        logger.error("Missing env: WECOM_TOKEN or WECOM_ENCODING_AES_KEY")
        return PlainTextResponse("server env misconfigured", status_code=500)

    # 验证签名并解密
    try:
        verifier = WeComURLVerifier(token=WECOM_TOKEN, encoding_aes_key=WECOM_ENCODING_AES_KEY, corp_id=WECOM_CORP_ID)
        ok, plain = verifier.verify_url(
            msg_signature=msg_signature,
            timestamp=timestamp,
            nonce=nonce,
            echostr=echostr,
        )
        if not ok:
            return PlainTextResponse("invalid signature", status_code=400)
        return PlainTextResponse(plain)
    except Exception as e:
        logger.exception("wecom_callback error: %s", e)
        return PlainTextResponse("internal error", status_code=500)

@app.post("/wecom/callback")
async def wecom_callback_post(
    request: Request,
    body: Annotated[dict, Body(...)],
    msg_signature: str = Query(..., description="企业微信签名 msg_signature"),
    timestamp: str = Query(..., description="时间戳 timestamp（字符串）"),
    nonce: str = Query(..., description="随机串 nonce"),
):
    """企业微信回调 POST（新回调 JSON 模式：解密并被动回复“收到”）。"""

    # 读取 JSON 请求体并直接取 encrypt（签名中声明为 dict，无需再判断类型）
    encrypt = body.get("encrypt")
    if not isinstance(encrypt, str) or not encrypt:
        return PlainTextResponse("missing encrypt in body", status_code=400)

    # Query 参数由函数签名显式接收

    if not WECOM_TOKEN or not WECOM_ENCODING_AES_KEY:
        logger.error("Missing env: WECOM_TOKEN or WECOM_ENCODING_AES_KEY")
        return PlainTextResponse("server env misconfigured", status_code=500)

    # 解密
    try:
        crypto = WeComMessageCrypto(token=WECOM_TOKEN, encoding_aes_key=WECOM_ENCODING_AES_KEY, corp_id=WECOM_CORP_ID)
        plain_xml = crypto.decrypt_from_json(
            msg_signature=msg_signature,
            timestamp=str(timestamp),
            nonce=str(nonce),
            encrypt=encrypt,
        )
        # 解密出来的消息，实际是 JSON 格式，例如：
        # {
        #     "msgid": "xxx",
        #     "aibotid": "xxx", 
        #     "chattype": "single",
        #     "from": {"userid": "ZhangSan"},
        #     "msgtype": "text",
        #     "text": {"content": "hi"}
        # }
        logger.info("wecom_callback_post decrypted plain xml: %s", plain_xml)

        # 直接使用随机 UUID 作为流式消息 id
        import uuid
        stream_id = uuid.uuid4().hex

        # 构造“回复用户消息”的流式消息（明文需为字符串）
        reply_plain_json = {
            "msgtype": "stream",
            "stream": {
                "id": stream_id,
                "finish": True,
                "content": "收到",
            },
        }
        reply_plain_text = json.dumps(reply_plain_json, ensure_ascii=False)

        encrypted_resp = crypto.encrypt_to_json(
            plain_text=reply_plain_text,
            nonce=str(nonce),
        )

        return JSONResponse(content=encrypted_resp)
    except InvalidSignatureException:
        return PlainTextResponse("invalid signature", status_code=400)
    except Exception as e:
        logger.exception("wecom_callback_post decrypt error: %s", e)
        return PlainTextResponse("internal error", status_code=500)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
