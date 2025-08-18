# 任务：实现CD功能 - 自动部署工作流

## 任务描述

实现deploy.yml文件，当main分支的"Build and Push"工作流构建成功后，自动部署到服务器。工作流应该使用新的稳定版本的GitHub Actions。

## 任务目标

- 创建 `.github/workflows/deploy.yml` 工作流文件
- 实现基于workflow_run的触发机制，监听"Build and Push"工作流完成
- 仅在构建成功时执行部署
- 支持手动触发（workflow_dispatch）
- 使用最新稳定版本的appleboy/ssh-action
- 使用GitHub secrets和vars管理服务器连接配置

## 技术方案

### 触发条件
- `workflow_run`: 监听"Build and Push"工作流在main分支完成
- `workflow_dispatch`: 支持手动触发

### 执行条件
- 仅在"Build and Push"工作流成功完成时执行
- 支持手动触发时无条件执行

### GitHub Actions 版本选择
- `appleboy/ssh-action@v1.0.3` - SSH部署动作的稳定版本

### 环境变量配置
```yaml
# 使用GitHub secrets和vars：
# vars.SERVER_SSH_HOST - 服务器主机地址
# secrets.SERVER_SSH_USER - SSH用户名
# secrets.SERVER_SSH_KEY - SSH私钥
# vars.SERVER_SSH_SCRIPT - 部署脚本
```

## 预期目录结构

```
.github/workflows/
├── build-push.yml    # 现有：构建推送工作流
├── deploy.yml        # 新增：部署工作流
├── only-build.yml    # 现有：仅构建工作流
└── ...               # 其他现有工作流
```

## 任务步骤

1. [ ] 分析现有build-push.yml工作流结构和命名
2. [ ] 创建deploy.yml工作流文件
3. [ ] 实现workflow_run触发机制
4. [ ] 配置SSH部署动作
5. [ ] 测试工作流配置语法
6. [ ] 验证环境变量和密钥配置（需要在实际环境中测试）

## 验收标准

- deploy.yml文件语法正确
- 正确监听"Build and Push"工作流完成事件
- 仅在构建成功时触发部署
- 支持手动触发
- 使用指定的SSH action稳定版本
- 正确引用所需的secrets和vars

## 里程碑与产出

- [ ] M1：创建基础工作流文件结构
- [ ] M2：实现workflow_run触发和条件判断
- [ ] M3：配置SSH部署动作
- [ ] M4：工作流文件语法验证

## 状态

进行中