# 企业微信回调消息处理（POST 接收与加解密回复）

## 任务描述
实现企业微信回调 POST 接口：接收加密的回调消息（新回调模式，JSON 载荷，`{"encrypt": "..."}`），完成解密、解析，并被动回复固定文本“收到”（加密后返回）。

## 任务目标
1. 实现 `/wecom/callback` 的 POST 接口，读取并记录请求消息体
2. 使用 `wechatpy.enterprise.crypto.WeChatCrypto` 完成消息加解密
3. 解析明文 XML，构造文本型“收到”的被动回复，并加密返回
4. 编写测试验证加解密流程与接口行为

## 技术方案
- 框架：FastAPI（实现回调路由与响应）
- 加解密：`wechatpy.enterprise.crypto.WeChatCrypto`
  - 新回调模式为 JSON 请求体，取出 `encrypt` 字段参与签名校验与解密
  - 解密：`decrypt_message`（传入密文结构体；JSON 模式需包装为 crypto 可识别的结构）或直接使用底层 AES 解密辅助方法（如已有封装）
  - 加密：`encrypt_message(plain_xml, nonce, timestamp)`（输出加密包体，再按新回调模式拼装 JSON 响应）
- 配置项：
  - `WECOM_TOKEN`：签名用 Token
  - `WECOM_AES_KEY`：EncodingAESKey
  - `WECOM_CORP_ID`：企业 ID（CorpID）
  - 建议通过环境变量或配置文件注入
- 明文格式与构造：
  - 明文仍为 XML（企业微信标准消息体：`FromUserName`、`ToUserName`、`MsgType`、`Content` 等）
  - 回复明文 XML：文本消息，内容固定为“收到”

## 接口设计
- **URL**: `/wecom/callback`
- **Method**: POST
- **Query**:
  - `msg_signature`: 回调签名
  - `timestamp`: 时间戳
  - `nonce`: 随机数
- **请求头**：`Content-Type: application/json`
- **请求体（JSON, 加密）示例（与你的线上抓包一致）**：
  ```json
{"encrypt":"IJH53zaBH\/jwpXeItM8OwgsmEI5po9PQltO8LN3H0noQUL2CHsx8YJnJ53wdrIisrb0mELqLP2ap4oySflfbAzxUfOZsSKGDj0Hey\/3eNaPiOGkocs5sAXyWKpZZb7GbkwN08Y+trQ5tw3AldXG8dJv3U5OhgIwobIbDKcfdpBKOa4xfU0rb0ODuxF1T8o\/hGei1wKbHLrMnhMY2NVs693aGORE2pZEhaHZUIPRrX56e\/x\/uzMqBQX1K26iX+zaLwdQOF9r6+faFjEcwmxtFBwd8zgy0hbuXfsKOlR\/5Nb4="
}
  ```
- **响应**：`Content-Type: application/json`，返回加密后的被动回复 JSON 包，明文内容为“收到”。
  - 响应 JSON 字段：`msg_signature`、`timestamp`、`nonce`、`encrypt`
  - 其中 `encrypt` 为对明文 XML 回复体进行加密后的密文

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
    - 提供合法 `msg_signature/timestamp/nonce` 与加密 JSON（含 `encrypt`），请求返回 200，且响应体为加密 JSON（含 `encrypt`）
    - 验证 `WeChatCrypto` 的签名校验与加解密参数（JSON 模式下对 `encrypt` 的处理）
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
- 企业微信签名校验使用 `msg_signature/timestamp/nonce` 与密文体结合校验，请勿遗漏；新回调模式中参与校验的密文字段为请求体 JSON 的 `encrypt`
- 时间戳取整（秒），时区统一使用 UTC 或服务器本地时区，但需与平台兼容
- 文本编码统一使用 UTF-8，XML 中使用 `CDATA`
- 暂不做消息去重与持久化；后续如需支持多类型消息，可抽象 XML 解析/构造为独立模块
