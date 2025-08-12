from fastapi import FastAPI
import uvicorn
from utils import register_exception_handlers
from utils.logging import init_logging, get_logger
from utils.config import settings

app = FastAPI(
    title="FastAPI Demo",
    description="A simple FastAPI application",
    version="1.0.0"
)

init_logging(settings.LOG_LEVEL)
logger = get_logger()

# 加载 .env 已由 utils.config.Settings 完成


# 装配全局异常处理器
register_exception_handlers(app)

# 挂载路由（echo、wecom callback 等）
from controller.echo_controller import router as echo_router
from controller.wecom_callback_controller import router as wecom_router
app.include_router(echo_router)
app.include_router(wecom_router)

# 记录配置信息用于调试
logger.info(f"token: {settings.WECOM_TOKEN} encoding_aes_key: {settings.WECOM_ENCODING_AES_KEY} corp_id: {settings.WECOM_CORP_ID}")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
