from wecom import WeComMessageCrypto
from wechatpy.exceptions import InvalidSignatureException


def create_crypto() -> WeComMessageCrypto:
    # token / encoding_aes_key / corp_id 的值在单测中不重要，因为 decrypt_message 将被打桩
    # encoding_aes_key 需要满足 43 位长度要求
    return WeComMessageCrypto(token="t", encoding_aes_key="a" * 43, corp_id="cid")


def test_decrypt_from_json_success(mocker):
    mock_crypto_cls = mocker.patch("wecom.crypto.WeChatCrypto")
    mock_crypto_cls.return_value.decrypt_message.return_value = "<xml>plain</xml>"

    crypto = create_crypto()
    plain = crypto.decrypt_from_json(
        msg_signature="sig",
        timestamp="123",
        nonce="n",
        body={"encrypt": "ENC"},
    )

    assert plain == "<xml>plain</xml>"
    # 验证 wechatpy.decrypt_message 被以包装后的 XML 调用
    args, kwargs = mock_crypto_cls.return_value.decrypt_message.call_args
    assert "<xml><Encrypt><![CDATA[ENC]]></Encrypt></xml>" in kwargs.get("msg")
    assert kwargs.get("signature") == "sig"
    assert kwargs.get("timestamp") == "123"
    assert kwargs.get("nonce") == "n"


def test_decrypt_from_json_invalid_signature(mocker):
    mock_crypto_cls = mocker.patch("wecom.crypto.WeChatCrypto")
    mock_crypto_cls.return_value.decrypt_message.side_effect = InvalidSignatureException("bad sig")

    crypto = create_crypto()
    try:
        crypto.decrypt_from_json(
            msg_signature="sig",
            timestamp="123",
            nonce="n",
            body={"encrypt": "ENC"},
        )
        assert False, "should raise InvalidSignatureException"
    except InvalidSignatureException:
        pass


def test_decrypt_from_json_missing_encrypt():
    crypto = create_crypto()
    try:
        crypto.decrypt_from_json(
            msg_signature="sig",
            timestamp="123",
            nonce="n",
            body={},
        )
        assert False, "should raise ValueError for missing encrypt"
    except ValueError:
        pass


