from wecom import WeComMessageCrypto
import json


# 使用用户提供的配置（与 verify 集成测试保持一致）
TOKEN = "eGsTQSJBs44yLCSq"
AES_KEY = "ENQ2J83KxaHtBMDswNRnBAza6O82y0u9e0wPfBMZIyu"
# 企业内部智能机器人场景，ReceiveId 为空字符串
CORP_ID = ""


def test_decrypt_from_json_success_integration():
    # 固定随机串，timestamp 由底层生成
    nonce = "1754668868"

    # 待加密的明文（JSON 字符串），解密应还原为同一 JSON 结构
    plain_obj = {
        "msgtype": "text",
        "text": {"content": "hi"},
    }
    plain_text = json.dumps(plain_obj, ensure_ascii=False)

    crypto = WeComMessageCrypto(token=TOKEN, encoding_aes_key=AES_KEY, corp_id=CORP_ID)

    # 使用 WeComMessageCrypto 加密（返回包含 encrypt/msgsignature/timestamp/nonce 的 JSON 字段）
    enc = crypto.encrypt_to_json(plain_text=plain_text, nonce=nonce)

    # 用返回的签名/时间戳/随机串/密文调用解密
    decrypted_text = crypto.decrypt_from_json(
        msg_signature=enc["msgsignature"],
        timestamp=str(enc["timestamp"]),
        nonce=enc["nonce"],
        body={"encrypt": enc["encrypt"]},
    )

    # 解析为对象对比结构等价，避免字符串序列化差异影响
    assert json.loads(decrypted_text) == plain_obj
