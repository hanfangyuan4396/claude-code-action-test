from fastapi import FastAPI, Request, Query
from fastapi.responses import PlainTextResponse
from wecom.verify import WeComURLVerifier
import os
import uvicorn
import logging
from pathlib import Path
from dotenv import load_dotenv

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
async def wecom_callback_post(request: Request):
    """企业微信回调 POST：仅打印收到的数据（参考 /echo POST）。

    当前实现：
    - 记录请求头、查询参数、原始请求体文本
    - 返回与 /echo POST 一致的 JSON 结构
    """

    headers = dict(request.headers)
    query_params = dict(request.query_params)

    try:
        body_bytes = await request.body()
        body_text = body_bytes.decode("utf-8", errors="ignore") if body_bytes else ""
    except Exception:
        body_text = ""

    logger.info(
        "wecom_callback_post method=%s url=%s headers=%s query=%s body=%s",
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

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
