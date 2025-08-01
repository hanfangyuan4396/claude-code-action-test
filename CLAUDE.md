# Claude 工作规范

## 任务处理流程

当提出一个新的需求的时候，先在tasks目录中创建一个任务文档，和用户讨论完善这个任务文档，然后再根据任务文档执行任务，而不是立即执行任务。

## 任务文档模板

每个新任务都应该在 `docs/tasks/` 目录中创建一个markdown文档，**必须包含**：
- 任务描述
- 任务目标

**可选包含**：
- 技术方案
- 预期目录结构
- 待讨论事项
- 任务步骤

## 工作流程
1. 创建任务文档
2. 与用户讨论完善
3. 根据确认后的文档执行任务
4. 在任务文档中更新任务状态，任务状态是增量更新，不要覆盖之前的任务状态