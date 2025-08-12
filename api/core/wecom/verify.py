"""
企业微信URL验证模块
基于 wechatpy 封装实现
核心层实现：仅包含验证算法，不依赖具体Web框架
"""

from wechatpy.enterprise.crypto import WeChatCrypto
from wechatpy.exceptions import InvalidSignatureException
import logging

logger = logging.getLogger(__name__)


class WeComURLVerifier:
    """企业微信URL验证器 - 核心层实现"""
    
    def __init__(self, token: str, encoding_aes_key: str, corp_id: str | None = None):
        """
        初始化验证器
        
        Args:
            token: 企业微信后台设置的Token
            encoding_aes_key: 企业微信后台设置的EncodingAESKey
            corp_id: 企业微信CorpID（内部自建应用为CorpID；企业内部智能机器人场景下传空字符串或不传）
        """
        self.token = token
        # 企业内部智能机器人场景中，ReceiveId 为空字符串
        self.corp_id = corp_id or ""
        try:
            self.crypto = WeChatCrypto(self.token, encoding_aes_key, self.corp_id)
        except Exception as e:
            logger.error(f"Failed to init WeChatCrypto: {e}")
            raise
    
    def verify_url(self, msg_signature: str, timestamp: str, nonce: str, echostr: str) -> tuple[bool, str]:
        """
        验证企业微信回调URL有效性
        
        Args:
            msg_signature: 签名串
            timestamp: 时间戳
            nonce: 随机串
            echostr: 加密字符串
            
        Returns:
            (验证是否成功, 解密后的echostr)
        """
        try:
            plain = self.crypto.check_signature(
                signature=msg_signature,
                timestamp=timestamp,
                nonce=nonce,
                echo_str=echostr,
            )
            return True, plain
        except InvalidSignatureException as e:
            logger.warning(f"Signature verification failed: {e}")
            return False, ""
        except Exception as e:
            logger.error(f"URL verification error: {e}")
            return False, ""
