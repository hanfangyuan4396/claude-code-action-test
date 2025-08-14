"""
企业微信业务服务层
承载企业微信回调处理、消息组装等业务逻辑，不依赖具体Web框架
"""

import json
import uuid
from typing import Any

from wechatpy.exceptions import InvalidSignatureException

from core.stream_manager import StreamStatus, get_stream_state, start_stream
from core.wecom.crypto import WeComMessageCrypto
from core.wecom.verify import WeComURLVerifier
from utils.logging import get_logger

logger = get_logger()


class WeComService:
    """企业微信业务服务类"""

    def __init__(self, token: str, encoding_aes_key: str, corp_id: str | None = None):
        """
        初始化企业微信服务

        Args:
            token: 企业微信后台设置的Token
            encoding_aes_key: 企业微信后台设置的EncodingAESKey
            corp_id: 企业微信CorpID
        """
        self.token = token
        self.encoding_aes_key = encoding_aes_key
        self.corp_id = corp_id

        # 初始化核心组件（直接初始化，保持简单）
        self.url_verifier = WeComURLVerifier(
            token=self.token,
            encoding_aes_key=self.encoding_aes_key,
            corp_id=self.corp_id,
        )
        self.message_crypto = WeComMessageCrypto(
            token=self.token,
            encoding_aes_key=self.encoding_aes_key,
            corp_id=self.corp_id,
        )

    def verify_callback_url(self, msg_signature: str, timestamp: str, nonce: str, echostr: str) -> tuple[bool, str]:
        """
        验证企业微信回调URL有效性

        Args:
            msg_signature: 签名串
            timestamp: 时间戳
            nonce: 随机串
            echostr: 加密字符串

        Returns:
            (验证是否成功, 解密后的echostr或错误信息)
        """
        logger.debug(
            "处理企业微信URL验证: msg_signature=%s, timestamp=%s, nonce=%s, echostr=%s",
            msg_signature,
            timestamp,
            nonce,
            echostr,
        )

        try:
            success, plain_text = self.url_verifier.verify_url(
                msg_signature=msg_signature, timestamp=timestamp, nonce=nonce, echostr=echostr
            )

            if success:
                logger.debug("企业微信URL验证成功")
                return True, plain_text
            else:
                logger.warning("企业微信URL验证失败：签名无效")
                return False, "invalid signature"

        except Exception:
            logger.exception("企业微信URL验证异常")
            return False, "internal error"

    def validate_callback_params(
        self, msg_signature: str | None, timestamp: str | None, nonce: str | None, echostr: str | None
    ) -> tuple[bool, str]:
        """
        验证回调参数完整性

        Args:
            msg_signature: 签名串
            timestamp: 时间戳
            nonce: 随机串
            echostr: 加密字符串

        Returns:
            (参数是否有效, 错误信息)
        """
        if not all([msg_signature, timestamp, nonce, echostr]):
            missing_params = []
            if not msg_signature:
                missing_params.append("msg_signature")
            if not timestamp:
                missing_params.append("timestamp")
            if not nonce:
                missing_params.append("nonce")
            if not echostr:
                missing_params.append("echostr")

            error_msg = f"missing required query params: {', '.join(missing_params)}"
            logger.warning("参数校验失败: %s", error_msg)
            return False, error_msg

        return True, ""

    def process_callback_message(
        self, msg_signature: str, timestamp: str, nonce: str, encrypt: str
    ) -> tuple[bool, str, dict[str, Any] | None]:
        """
        处理企业微信回调消息（POST）

        Args:
            msg_signature: 签名串
            timestamp: 时间戳
            nonce: 随机串
            encrypt: 加密的消息内容

        Returns:
            (处理是否成功, 错误信息或成功标识, 加密的回复消息字典)
        """
        logger.debug("处理企业微信回调消息: msg_signature=%s, timestamp=%s, nonce=%s", msg_signature, timestamp, nonce)

        try:
            # 解密消息
            plain_text = self.message_crypto.decrypt_from_json(
                msg_signature=msg_signature,
                timestamp=str(timestamp),
                nonce=str(nonce),
                encrypt=encrypt,
            )

            # 解密出来的消息为明文 XML 字符串，业务上按 JSON 解析（企业微信新回调在明文中放 JSON）
            logger.debug("wecom_callback_post decrypted plain text: %s", plain_text)

            try:
                msg_obj = json.loads(plain_text)
            except Exception:
                # 若不是 JSON，回落到一次性结束的简单回包
                stream_id = uuid.uuid4().hex
                reply_plain_json = {
                    "msgtype": "stream",
                    "stream": {"id": stream_id, "finish": True, "content": "收到"},
                }
            else:
                msgtype = msg_obj.get("msgtype")
                # 处理拉取式刷新：WeCom 会携带 msgtype=stream 且附 stream.id
                if msgtype == "stream" and isinstance(msg_obj.get("stream"), dict):
                    sid = msg_obj["stream"].get("id")
                    state = get_stream_state(sid)
                    reply_plain_json = {
                        "msgtype": "stream",
                        "stream": {
                            "id": sid,
                            # 当状态为 DONE/ERROR/MISSING 时，认为轮询可以结束
                            "finish": state["status"] in (StreamStatus.DONE, StreamStatus.ERROR, StreamStatus.MISSING),
                            "content": state["content"],
                        },
                    }
                else:
                    # 首次收到用户消息：创建新的流会话，立即返回首包（finish=false）
                    # 这里以不同消息体类型统一提取一个 prompt（简单起见）
                    prompt = None
                    if msgtype == "text" and isinstance(msg_obj.get("text"), dict):
                        prompt = msg_obj["text"].get("content")
                    elif msgtype == "mixed" and isinstance(msg_obj.get("mixed"), dict):
                        prompt = json.dumps(msg_obj.get("mixed"))
                    elif msgtype == "image" and isinstance(msg_obj.get("image"), dict):
                        prompt = json.dumps(msg_obj.get("image"))
                    if not prompt:
                        prompt = ""

                    stream_id = start_stream(prompt)
                    # 首次响应返回空内容，finish=false，由后续轮询逐步取增量
                    reply_plain_json = {
                        "msgtype": "stream",
                        "stream": {"id": stream_id, "finish": False, "content": ""},
                    }
            reply_plain_text = json.dumps(reply_plain_json, ensure_ascii=False)

            # 加密回复
            encrypted_resp = self.message_crypto.encrypt_to_json(
                plain_text=reply_plain_text,
                nonce=str(nonce),
            )

            logger.info("企业微信回调消息处理成功")
            return True, "success", encrypted_resp

        except InvalidSignatureException as e:
            logger.warning("企业微信回调消息签名验证失败: %s", e)
            return False, "invalid signature", None
        except Exception:
            logger.exception("企业微信回调消息处理异常")
            return False, "internal error", None
