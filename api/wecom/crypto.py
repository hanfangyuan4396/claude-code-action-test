"""
企业微信消息加解密封装

- 面向“新回调模式”（JSON 体仅包含 encrypt 字段）
  通过将 JSON 中的密文字段包装为标准 XML 形式，复用 wechatpy 的 decrypt_message 能力
"""

from __future__ import annotations

from typing import Any, Dict
import json
import logging

from wechatpy.enterprise.crypto import WeChatCrypto
from wechatpy.exceptions import InvalidSignatureException


logger = logging.getLogger(__name__)


class WeComMessageCrypto:
    """企业微信消息加解密器

    参考 `WeComURLVerifier` 的初始化方式，封装 wechatpy 的加解密能力。
    仅先实现：从“新回调 JSON（含 encrypt）”解密出明文 XML。
    """

    def __init__(self, token: str, encoding_aes_key: str, corp_id: str | None = None) -> None:
        self.token = token
        # 企业内部智能机器人场景中，ReceiveId 为空字符串
        self.corp_id = corp_id or ""
        try:
            self.crypto = WeChatCrypto(self.token, encoding_aes_key, self.corp_id)
        except Exception as exc:  # pragma: no cover - 初始化失败直接抛出
            logger.error("Failed to init WeChatCrypto: %s", exc)
            raise

    def _ensure_encrypt_from_body(self, body: str | bytes | Dict[str, Any]) -> str:
        """从请求体中提取 encrypt 字段。

        支持传入：
        - 字典（已解析的 JSON）
        - 字符串/字节串（未解析的 JSON 文本）
        """
        if isinstance(body, (bytes, bytearray)):
            try:
                body = body.decode("utf-8")
            except Exception as exc:  # pragma: no cover - 解码异常很少出现
                raise ValueError("请求体字节串解码失败: 需为 UTF-8 编码") from exc

        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError as exc:
                raise ValueError("请求体需为合法的 JSON 字符串或字典") from exc

        if not isinstance(body, dict):
            raise ValueError("请求体类型错误: 需为字典或 JSON 字符串")

        encrypt = body.get("encrypt")
        if not isinstance(encrypt, str) or not encrypt:
            raise ValueError("请求体缺少 encrypt 字段或其值非法")
        return encrypt

    def decrypt_from_json(self, msg_signature: str, timestamp: str, nonce: str, body: str | bytes | Dict[str, Any]) -> str:
        """解密“新回调模式”JSON 请求体，返回明文 XML 字符串。

        Args:
            msg_signature: 回调签名
            timestamp: 时间戳（字符串）
            nonce: 随机数
            body: JSON 请求体（可为 dict、JSON 字符串或字节串），需包含 encrypt 字段

        Returns:
            明文 XML 字符串

        Raises:
            ValueError: 入参不合法或 JSON 结构缺失
            InvalidSignatureException: 签名校验失败
            Exception: 其他底层解密异常
        """
        encrypt = self._ensure_encrypt_from_body(body)

        # wechatpy 的 decrypt_message 期望传入 XML 格式的密文包体：
        #   <xml><Encrypt><![CDATA[...]]></Encrypt></xml>
        encrypted_xml = f"<xml><Encrypt><![CDATA[{encrypt}]]></Encrypt></xml>"

        try:
            plain_xml: str = self.crypto.decrypt_message(
                msg=encrypted_xml,
                signature=msg_signature,
                timestamp=timestamp,
                nonce=nonce,
            )
            return plain_xml
        except InvalidSignatureException:
            # 透传给上层以便返回 400
            raise
        except Exception as exc:
            logger.error("Decrypt message failed: %s", exc)
            raise
