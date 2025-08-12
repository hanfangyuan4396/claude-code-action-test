# 后端代码重构任务

## 任务描述
将现有后端代码进行分层重构，按照“入口 → 控制器层（controller）→ 业务层（service）→ 核心层（core）→ 通用工具（utils）”的架构组织代码，提升可读性、可维护性与可测试性。在重构过程中保持对外接口行为不变，确保现有测试用例继续通过。

## 任务目标
- 规范项目目录结构，解耦路由与业务逻辑
- 通用能力（配置、日志等）统一收敛至 `utils`
- `core` 仅承载 WeCom 领域相关能力，其他与框架无关的通用能力不放在 `core`
- 将接口层逻辑收敛在 `controller`，业务逻辑下沉到 `service`
- 保持现有 API 行为与兼容性，单元/集成测试全部通过

## 技术方案
- 框架：FastAPI + Pydantic
- 分层约定：
  - `app.py` 仅负责应用初始化、挂载路由、注册依赖
  - `controller` 只做协议适配（路由、请求/响应 DTO、参数校验），调用 `service`
  - `service` 聚合业务流程与领域逻辑，不依赖具体 Web 框架
  - `core/wecom` 承载 WeCom 领域能力（如签名校验、加解密等）
  - `utils` 承载跨业务通用能力（配置、日志、错误处理等）
  - 错误处理：在 `utils` 中实现全局兜底异常处理器（例如 `utils/error_handlers.py`），并在 `app.py` 中完成注册/装配。`controller` 层按需返回业务错误（明确的 4xx/5xx），未捕获异常由全局处理器统一返回 JSON 错误响应

## 预期目录结构
```
api/
├── app.py                     # 应用入口
├── controller/                # 控制器层：路由与协议适配
│   ├── __init__.py
│   ├── health.py              # 健康检查/基础路由示例
│   └── wecom_callback.py      # 企业微信回调相关路由
├── service/                   # 业务层：领域逻辑
│   ├── __init__.py
│   └── wecom_service.py       # 企业微信回调处理、消息组装
├── core/                      # 核心领域能力（仅 WeCom 相关）
│   ├── __init__.py
│   └── wecom/
│       ├── __init__.py
│       ├── crypto.py          # 加解密/签名等底层算法
│       └── verify.py          # URL 验证/签名校验封装（可选）
└── utils/                     # 通用工具：配置、日志、错误处理等
    ├── __init__.py
    ├── config.py              # 配置加载（env/文件）
    ├── logging.py             # 日志初始化
    └── error_handlers.py      # 全局异常处理器定义（供 app 装配）
```

## 迁移映射（现状 → 重构后）
- `api/app.py` → 保留为入口；拆分路由至 `api/controller/*`，初始化逻辑留在 `app.py`；日志初始化迁移至 `api/utils/logging.py`
- `api/wecom/crypto.py` → `api/core/wecom/crypto.py`
- `api/wecom/verify.py` → `api/core/wecom/verify.py`（领域算法）+ `api/service/wecom_service.py`（业务流程封装）
- 回调/消息解析相关函数 → `api/service/wecom_service.py`（流程编排，必要时内联处理 XML/JSON，不抽出独立 `xml_utils.py`）
- 原在 `core` 计划中的配置/日志等通用能力，统一迁移至 `api/utils`（`config.py`、`logging.py`、`error_handlers.py`）
- 测试：`api/tests/**` 保持路径不变，必要时更新导入路径与用例适配

## 实施步骤
1. 盘点现有模块与入口，标注外部可见行为与测试覆盖面
2. 创建分层目录骨架与 `__init__.py`：新增 `core/wecom` 与 `utils`
3. 从 `api/app.py` 中抽离路由至 `api/controller/*`；日志初始化迁移至 `utils.logging`；全局异常处理器实现迁移至 `utils.error_handlers`，在 `app.py` 中装配注册
4. 抽取业务逻辑至 `api/service/wecom_service.py`，`controller` 仅保留入参校验与调用
5. 迁移加解密与校验能力：`wecom/crypto.py`、`wecom/verify.py` → `core/wecom/*`
6. 将通用配置/日志/错误处理迁移至 `api/utils`，在 `app.py` 中完成装配
7. 调整导入路径；运行单元/集成测试，逐步修复
8. 补充/更新必要测试，确保行为兼容与边界条件覆盖
9. 更新 `api/README.md` 及相关文档，说明分层规范与入口用法

## 验收标准
- 目录结构与分层职责符合本任务文档约定
- 所有现有测试与新增测试通过（含 CI）
- 主要接口对外行为保持兼容（入参/出参/状态码）
- 代码通过静态检查与 Lint 规则

## 待讨论事项
- `core/wecom` 下文件边界（是否将 URL 验证与消息加解密拆分为独立模块）
- 路由分组与前缀（例如 `/wecom`）的最终约定
- 错误处理：已确认采用在 `utils` 中实现全局兜底异常处理器、并在 `app.py` 注册装配的方案（`controller` 层仅做必要的业务错误响应）

## 里程碑与产出
- M1：目录骨架、`app.py` 装配、基础路由拆分
- M2：`wecom` 相关逻辑迁移完成，测试可运行
- M3：全部测试通过，文档更新，完成交付
