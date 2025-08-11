from wecom import WeComMessageCrypto
from wechatpy.enterprise.crypto import WeChatCrypto
import xml.etree.ElementTree as ET


# 使用用户提供的配置（与 verify 集成测试保持一致）
TOKEN = "eGsTQSJBs44yLCSq"
AES_KEY = "ENQ2J83KxaHtBMDswNRnBAza6O82y0u9e0wPfBMZIyu"
# 企业内部智能机器人场景，ReceiveId 为空字符串
CORP_ID = ""


def test_decrypt_from_json_success_integration():
    crypto_sdk = WeChatCrypto(TOKEN, AES_KEY, CORP_ID)

    # 固定时间戳与随机串，保证结果可复现
    nonce = "1754668868"
    timestamp = "1754796900"

    # 待加密的明文（POST 解密后应返回该明文）
    plain_xml = "<xml><FromUserName><![CDATA[u]]></FromUserName><ToUserName><![CDATA[v]]></ToUserName><MsgType><![CDATA[text]]></MsgType><Content><![CDATA[hi]]></Content></xml>"
    # 使用 wechatpy 生成一组有效的密文与签名（与 URL 验证不同，这里我们只取 Encrypt，然后自己签名）
    encrypted_xml = crypto_sdk.encrypt_message(plain_xml, nonce, timestamp)

    # 解析出 Encrypt
    root = ET.fromstring(encrypted_xml)
    encrypt = root.findtext("Encrypt")

    # wechatpy 的 check_signature/ decrypt_message 在 decrypt_message 内部会做签名校验
    # 因此对调用方来说，准备 msg_signature/timestamp/nonce 即可
    # 这里直接复用集成加密过程得到的 MsgSignature/TimeStamp/Nonce
    msg_signature = root.findtext("MsgSignature")
    ts = root.findtext("TimeStamp")
    n = root.findtext("Nonce")

    crypto = WeComMessageCrypto(token=TOKEN, encoding_aes_key=AES_KEY, corp_id=CORP_ID)
    plain = crypto.decrypt_from_json(
        msg_signature=msg_signature,
        timestamp=ts,
        nonce=n,
        body={"encrypt": encrypt},
    )

    assert plain == plain_xml
