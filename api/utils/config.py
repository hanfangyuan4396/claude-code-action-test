import os
from pathlib import Path
from dotenv import load_dotenv


class ConfigValidationError(Exception):
    """配置校验异常"""
    pass


class Settings:
    def __init__(self) -> None:
        # 加载 .env（位于与 app.py 同目录的 .env）
        env_path = Path(__file__).with_name("..").resolve().joinpath(".env")
        # 兜底：如果上面路径不对，尝试 api 根目录
        if not env_path.exists():
            env_path = Path(__file__).resolve().parents[1].joinpath(".env")
        load_dotenv(dotenv_path=env_path)

        self.WECOM_TOKEN: str | None = os.getenv("WECOM_TOKEN")
        self.WECOM_ENCODING_AES_KEY: str | None = os.getenv("WECOM_ENCODING_AES_KEY")
        self.WECOM_CORP_ID: str = os.getenv("WECOM_CORP_ID", "")
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
        
        # 配置完整性校验
        self._validate_config()
    
    def _validate_config(self) -> None:
        """
        验证配置完整性
        
        Raises:
            ConfigValidationError: 当配置不完整时抛出异常
        """
        missing_config = []
        
        if not self.WECOM_TOKEN:
            missing_config.append("WECOM_TOKEN")
        if not self.WECOM_ENCODING_AES_KEY:
            missing_config.append("WECOM_ENCODING_AES_KEY")
        
        if missing_config:
            error_msg = f"missing env: {', '.join(missing_config)}"
            raise ConfigValidationError(error_msg)


settings = Settings()


