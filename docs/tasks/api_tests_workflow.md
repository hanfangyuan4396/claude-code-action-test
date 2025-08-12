# API 测试工作流（技术方案草案 - 精简版）

## 任务描述
为本项目的 API 模块（目录 `api/`）设计一个精简的 CI 测试工作流方案，用于在 Pull Request 上自动执行测试。该方案此阶段仅讨论功能与范围，不包含具体 YAML 配置。

## 任务目标
- 在 PR 场景下自动化运行 API 测试，给出清晰的通过/失败与覆盖率反馈。
- 仅实现最小可行（MVP），不引入额外质量检查与外部依赖。

## 当前测试现状
- 测试目录：`api/tests/`
  - 单元测试：`api/tests/unit_tests/`
  - 轻量集成测试：`api/tests/integration_tests/`
  - `conftest.py`：处理 `sys.path` 以保证从 `api/` 根可导入包。
- `pytest.ini` 已配置 `testpaths = tests`。

## MVP 功能清单（不含实现细节）
1. 触发条件
   - 当 PR 影响 `api/**` 或测试相关配置时，自动触发。

2. Python 运行环境
   - 仅支持 Python 3.12。

3. 依赖安装
   - 基于 `api/requirements.txt` 安装依赖。

4. 运行测试
   - 执行 `pytest` 覆盖 `api/tests/` 下的用例（含单测与轻量级集成测试）。
   - 不启动或依赖任何外部服务（如 Redis、MySQL 等）。

5. 覆盖率产出与汇总
   - 输出终端覆盖率（term-missing）。
   - 可生成 JSON 覆盖率并在 PR Summary 展示覆盖率百分比。


## 范围外（此阶段不做）
- 外部依赖或容器化环境（Redis、MySQL、消息队列、向量数据库等）。
- 端到端（E2E）或前端测试集成。
- 代码风格/类型检查（ruff、mypy 等）与覆盖率阈值门禁。

## 产出
- 一份最终的 CI 工作流 YAML（后续阶段提交）。
- 在 `api/README.md` 中补充简要的本地测试说明。
