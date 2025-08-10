from wecom.verify import WeComURLVerifier
from wechatpy.enterprise.crypto import WeChatCrypto
import xml.etree.ElementTree as ET


# 使用用户提供的配置
TOKEN = "eGsTQSJBs44yLCSq"
AES_KEY = "ENQ2J83KxaHtBMDswNRnBAza6O82y0u9e0wPfBMZIyu"
# 企业内部智能机器人场景，ReceiveId 为空字符串
CORP_ID = ""


def test_verify_url_success_integration():
    crypto = WeChatCrypto(TOKEN, AES_KEY, CORP_ID)

    # 固定时间戳与随机串，保证结果可复现
    nonce = "1754668868"
    timestamp = "1754796900"

    # 待加密的明文（URL 验证解密后应返回该明文）
    plain_xml = "<xml><Test>Hello</Test></xml>"

    # 使用 wechatpy 生成一组有效的密文与签名
    encrypted_xml = crypto.encrypt_message(plain_xml, nonce, timestamp)

    # 解析出 Encrypt / MsgSignature / TimeStamp / Nonce
    root = ET.fromstring(encrypted_xml)
    echostr = root.findtext("Encrypt")
    msg_signature = root.findtext("MsgSignature")
    ts = root.findtext("TimeStamp")
    n = root.findtext("Nonce")

    verifier = WeComURLVerifier(token=TOKEN, encoding_aes_key=AES_KEY, corp_id=CORP_ID)
    ok, plain = verifier.verify_url(
        msg_signature=msg_signature,
        timestamp=ts,
        nonce=n,
        echostr=echostr,
    )

    assert ok is True
    assert plain == plain_xml
