"""
企业微信消息加解密封装

- 面向“新回调模式”（JSON 体仅包含 encrypt 字段）
  通过将 JSON 中的密文字段包装为标准 XML 形式，复用 wechatpy 的 decrypt_message 能力
"""

from __future__ import annotations

from typing import Any, Dict
import json
import logging
import xml.etree.ElementTree as ET

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
    
    # TODO: 删除此函数，解密函数直接传入待解密的密文
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

    def encrypt_to_json(self, plain_text: str, nonce: str) -> Dict[str, Any]:
        """将明文字符串加密并按新回调 JSON 协议返回。

        注意：本方法仅接受字符串。调用方需在调用前自行将 JSON/dict/bytes 等格式转换为字符串。

        输出字段：`encrypt`, `msgsignature`, `timestamp`, `nonce`。

        Args:
            plain_text: 明文字符串
            nonce: 随机串（建议使用回调 URL 中的 nonce 原样回传）

        Returns:
            JSON 字段字典

        Raises:
            ValueError: 当 wechatpy 返回的加密 XML 结构不完整或入参类型错误时
            Exception: 其他底层加密异常
        """
        if not isinstance(plain_text, str):
            raise ValueError("待加密明文只支持字符串，调用方需自行转换为字符串")

        try:
            # timestamp 留空，由 wechatpy 内部生成
            encrypted_xml: str = self.crypto.encrypt_message(plain_text, nonce)
        except Exception as exc:
            logger.error("Encrypt message failed: %s", exc)
            raise

        try:
            root = ET.fromstring(encrypted_xml)
        except Exception as exc:
            logger.error("Parse encrypted xml failed: %s", exc)
            raise

        encrypt_text = root.findtext("Encrypt")
        msg_sig = root.findtext("MsgSignature")
        ts = root.findtext("TimeStamp")
        n = root.findtext("Nonce")

        if not all([encrypt_text, msg_sig, ts, n]):
            raise ValueError("加密结果缺少必要字段: Encrypt/MsgSignature/TimeStamp/Nonce")

        # 与企业微信文档一致，字段名采用 msgsignature/timestamp/nonce
        return {
            "encrypt": encrypt_text,
            "msgsignature": msg_sig,
            "timestamp": int(ts) if str(ts).isdigit() else ts,
            "nonce": n,
        }
