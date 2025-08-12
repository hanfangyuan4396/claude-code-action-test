"""
企业微信业务服务层
承载企业微信回调处理、消息组装等业务逻辑，不依赖具体Web框架
"""

from typing import Tuple, Optional, Dict, Any
import json
import uuid
from core.wecom.verify import WeComURLVerifier
from core.wecom.crypto import WeComMessageCrypto
from wechatpy.exceptions import InvalidSignatureException
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
    
    def verify_callback_url(
        self,
        msg_signature: str,
        timestamp: str,
        nonce: str,
        echostr: str
    ) -> Tuple[bool, str]:
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
        logger.info(
            "处理企业微信URL验证: msg_signature=%s, timestamp=%s, nonce=%s, echostr=%s",
            msg_signature, timestamp, nonce, echostr
        )
        
        try:
            success, plain_text = self.url_verifier.verify_url(
                msg_signature=msg_signature,
                timestamp=timestamp,
                nonce=nonce,
                echostr=echostr
            )
            
            if success:
                logger.info("企业微信URL验证成功")
                return True, plain_text
            else:
                logger.warning("企业微信URL验证失败：签名无效")
                return False, "invalid signature"
                
        except Exception as e:
            logger.exception("企业微信URL验证异常: %s", e)
            return False, "internal error"
    
    def validate_callback_params(
        self,
        msg_signature: Optional[str],
        timestamp: Optional[str],
        nonce: Optional[str],
        echostr: Optional[str]
    ) -> Tuple[bool, str]:
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
        self,
        msg_signature: str,
        timestamp: str,
        nonce: str,
        encrypt: str
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
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
        logger.info(
            "处理企业微信回调消息: msg_signature=%s, timestamp=%s, nonce=%s",
            msg_signature, timestamp, nonce
        )
        
        try:
            # 解密消息
            plain_text = self.message_crypto.decrypt_from_json(
                msg_signature=msg_signature,
                timestamp=str(timestamp),
                nonce=str(nonce),
                encrypt=encrypt,
            )
            
            # 解密出来的消息，实际是 JSON 格式
            logger.info("wecom_callback_post decrypted plain text: %s", plain_text)
            
            # 直接使用随机 UUID 作为流式消息 id
            stream_id = uuid.uuid4().hex
            
            # 构造"回复用户消息"的流式消息（明文需为字符串）
            reply_plain_json = {
                "msgtype": "stream",
                "stream": {
                    "id": stream_id,
                    "finish": True,
                    "content": "收到",
                },
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
        except Exception as e:
            logger.exception("企业微信回调消息处理异常: %s", e)
            return False, "internal error", None
