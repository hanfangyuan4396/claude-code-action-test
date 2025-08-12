"""
企业微信消息加解密封装 - 核心层实现

- 面向"新回调模式"（JSON 体仅包含 encrypt 字段）
  通过将 JSON 中的密文字段包装为标准 XML 形式，复用 wechatpy 的 decrypt_message 能力
- 核心层实现：仅包含加解密算法，不依赖具体Web框架
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from typing import Any

from wechatpy.enterprise.crypto import WeChatCrypto
from wechatpy.exceptions import InvalidSignatureException

logger = logging.getLogger(__name__)


class WeComMessageCrypto:
    """企业微信消息加解密器 - 核心层实现

    参考 `WeComURLVerifier` 的初始化方式，封装 wechatpy 的加解密能力。
    仅先实现：从"新回调 JSON（含 encrypt）"解密出明文 XML。
    """

    def __init__(self, token: str, encoding_aes_key: str, corp_id: str | None = None) -> None:
        self.token = token
        # 企业内部智能机器人场景中，ReceiveId 为空字符串
        self.corp_id = corp_id or ""
        try:
            self.crypto = WeChatCrypto(self.token, encoding_aes_key, self.corp_id)
        except Exception:  # pragma: no cover - 初始化失败直接抛出
            logger.exception("Failed to init WeChatCrypto")
            raise

    def decrypt_from_json(self, msg_signature: str, timestamp: str, nonce: str, encrypt: str) -> str:
        """解密"新回调模式"回调密文，返回明文 XML 字符串。

        Args:
            msg_signature: 回调签名
            timestamp: 时间戳（字符串）
            nonce: 随机数
            encrypt: 待解密的密文字符串（来自请求体的 encrypt 字段）

        Returns:
            明文 XML 字符串

        Raises:
            ValueError: 入参不合法（encrypt 非法）
            InvalidSignatureException: 签名校验失败
            Exception: 其他底层解密异常
        """
        if not isinstance(encrypt, str) or not encrypt:
            raise ValueError("待解密的 encrypt 需为非空字符串")

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

    def encrypt_to_json(self, plain_text: str, nonce: str) -> dict[str, Any]:
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
        except Exception:
            logger.exception("Encrypt message failed")
            raise

        try:
            root = ET.fromstring(encrypted_xml)
        except Exception:
            logger.exception("Parse encrypted xml failed")
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
