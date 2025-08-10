from fastapi import FastAPI, Request
import uvicorn
import logging

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

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)