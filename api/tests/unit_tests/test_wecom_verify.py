from wecom.verify import WeComURLVerifier
from wechatpy.exceptions import InvalidSignatureException


def create_verifier() -> WeComURLVerifier:
    # token / encoding_aes_key / corp_id 的值在单测中不重要，因为 check_signature 已被打桩
    # encoding_aes_key 需要满足 43 位长度要求
    return WeComURLVerifier(token="t", encoding_aes_key="a" * 43, corp_id="cid")


def test_verify_url_success(mocker):
    mock_crypto = mocker.patch("wecom.verify.WeChatCrypto")
    mock_crypto.return_value.check_signature.return_value = "plain_echostr"

    verifier = create_verifier()
    ok, plain = verifier.verify_url(
        msg_signature="sig",
        timestamp="123",
        nonce="n",
        echostr="enc",
    )

    assert ok is True
    assert plain == "plain_echostr"


def test_verify_url_invalid_signature(mocker):
    mock_crypto = mocker.patch("wecom.verify.WeChatCrypto")
    mock_crypto.return_value.check_signature.side_effect = InvalidSignatureException("bad sig")

    verifier = create_verifier()
    ok, plain = verifier.verify_url(
        msg_signature="sig",
        timestamp="123",
        nonce="n",
        echostr="enc",
    )

    assert ok is False
    assert plain == ""


def test_verify_url_unexpected_error(mocker):
    mock_crypto = mocker.patch("wecom.verify.WeChatCrypto")
    mock_crypto.return_value.check_signature.side_effect = RuntimeError("boom")

    verifier = create_verifier()
    ok, plain = verifier.verify_url(
        msg_signature="sig",
        timestamp="123",
        nonce="n",
        echostr="enc",
    )

    assert ok is False
    assert plain == ""
