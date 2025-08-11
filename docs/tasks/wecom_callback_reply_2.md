# 企业微信回调消息处理（POST 接收与加解密回复）

## 任务描述
实现企业微信回调 POST 接口：接收加密的回调消息，完成解密、解析，并被动回复固定文本“收到”（加密后返回）。

## 任务目标
1. 实现 `/wecom/callback` 的 POST 接口，读取并记录请求消息体
2. 使用 `wechatpy.enterprise.crypto.WeChatCrypto` 完成消息加解密
3. 解析明文 XML，构造文本型“收到”的被动回复，并加密返回
4. 编写测试验证加解密流程与接口行为

## 技术方案
- 框架：FastAPI（实现回调路由与响应）
- 加解密：`wechatpy.enterprise.crypto.WeChatCrypto`
  - 解密：`decrypt_message(encrypt_xml, msg_signature, timestamp, nonce)`
  - 加密：`encrypt_message(plain_xml, nonce, timestamp)`
- 配置项：
  - `WECOM_TOKEN`：签名用 Token
  - `WECOM_AES_KEY`：EncodingAESKey
  - `WECOM_CORP_ID`：企业 ID（CorpID）
  - 建议通过环境变量或配置文件注入
- XML 解析与构造：
  - 解析明文 XML（`FromUserName`、`ToUserName`、`MsgType`、`Content` 等）
  - 回复明文 XML：文本消息，内容固定为“收到”

## 接口设计
- **URL**: `/wecom/callback`
- **Method**: POST
- **Query**:
  - `msg_signature`: 回调签名
  - `timestamp`: 时间戳
  - `nonce`: 随机数
- **请求体（XML, 加密）示例**：
  ```xml
  <xml>
    <ToUserName><![CDATA[ww1234567890]]></ToUserName>
    <Encrypt><![CDATA[密文]]></Encrypt>
    <AgentID><![CDATA[1000002]]></AgentID>
  </xml>
  ```
- **响应**：`Content-Type: application/xml`，加密后的被动回复 XML，明文内容为“收到”。

## 目录结构（建议）
```
api/
├── app.py                 # 在此实现 /wecom/callback 的 POST 处理函数
└── wecom/
    ├── crypto.py          # 在此实现/封装加解密类（基于 WeChatCrypto）
    └── __init__.py
```

## 测试计划
- 框架与工具：`pytest`、`pytest-mock`、、`pytest-cov`
- 用例覆盖：
  - 成功用例：
    - 提供合法 `msg_signature/timestamp/nonce` 与加密 XML，请求返回 200，且响应体为加密 XML
    - 验证 `WeChatCrypto.decrypt_message`、`encrypt_message` 的调用参数
    - 明文解析后，回复内容固定为“收到”
  - 失败用例：
    - 签名校验失败（抛 400）
    - 明文 XML 解析失败（抛 400）
    - 加密失败（抛 500）
- 环境变量通过 `monkeypatch` 注入模拟配置


## 验收标准
- 能正确接收企业微信 POST 回调，完成签名校验与消息解密
- 能根据明文 XML 构造文本“收到”的被动回复，完成加密并返回
- 单测覆盖主要正反向路径，关键分支均被验证

## 注意事项
- 企业微信签名校验使用 `msg_signature/timestamp/nonce` 与密文体结合校验，请勿遗漏
- 时间戳取整（秒），时区统一使用 UTC 或服务器本地时区，但需与平台兼容
- 文本编码统一使用 UTF-8，XML 中使用 `CDATA`
- 暂不做消息去重与持久化；后续如需支持多类型消息，可抽象 XML 解析/构造为独立模块
