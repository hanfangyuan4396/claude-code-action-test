# 任务：实现镜像构建与推送工作流

## 任务描述

为项目实现一个新的 GitHub Actions 工作流 `build-push.yml`，用于构建并推送 Docker 镜像到阿里云容器镜像服务。该工作流应该在 main 分支推送时自动触发，并支持手动触发。

## 任务目标

- 创建 `.github/workflows/build-push.yml` 工作流文件
- 实现自动化构建 API Docker 镜像
- 推送镜像到阿里云容器镜像服务
- 使用最新稳定版本的 GitHub Actions
- 支持基于文件变更的条件构建
- 使用环境变量和密钥管理凭据

## 技术方案

### 触发条件
- `push` 到 `main` 分支
- `workflow_dispatch` 手动触发

### 环境变量配置
```yaml
env:
  ALIYUN_REGISTRY: ${{ vars.ALIYUN_REGISTRY }}
  ALIYUN_REGISTRY_USER: ${{ secrets.ALIYUN_REGISTRY_USER }}
  ALIYUN_REGISTRY_PWD: ${{ secrets.ALIYUN_REGISTRY_PWD }}
  API_IMAGE_NAME: ${{ vars.API_IMAGE_NAME }}
```

### 主要作业
1. **changes** - 检测文件变更
   - 使用 `dorny/paths-filter@v3` 检测 `api/**` 和 `workflow/**` 变更
   
2. **api-build-and-push** - 构建并推送镜像
   - 使用最新版本的 Docker actions
   - 登录阿里云容器镜像服务
   - 提取元数据（标签、标注）
   - 构建并推送 Docker 镜像

### GitHub Actions 版本选择
基于当前 `only-build.yml` 已使用的稳定版本：
- `actions/checkout@v4`
- `docker/setup-buildx-action@v3`
- `docker/build-push-action@v6`
- `docker/login-action@v3`
- `docker/metadata-action@v5`
- `dorny/paths-filter@v3`

## 任务步骤

1. [x] 分析现有 `only-build.yml` 工作流结构
2. [x] 创建 `build-push.yml` 工作流文件
3. [x] 实现文件变更检测逻辑
4. [x] 配置阿里云容器镜像服务登录
5. [x] 实现 Docker 镜像构建和推送
6. [x] 测试工作流配置语法
7. [ ] 验证环境变量和密钥配置（需要在实际环境中测试）

## 预期目录结构

```
.github/workflows/
├── build-push.yml    # 新增：构建推送工作流
├── only-build.yml    # 现有：仅构建工作流
└── ...               # 其他现有工作流
```

## 待讨论事项

- 是否需要支持多架构构建（如 linux/amd64, linux/arm64）
- 镜像标签策略（基于分支、提交哈希还是元数据）
- 是否需要构建缓存优化
- 失败通知机制

## 里程碑与产出

- [x] M1：创建基础工作流文件结构
- [x] M2：实现文件变更检测和条件构建
- [x] M3：配置阿里云镜像仓库集成
- [x] M4：完成镜像构建和推送逻辑
- [x] M5：工作流文件语法验证和测试

## 实现细节

### 使用的 GitHub Actions 版本
- `actions/checkout@v4` - 最新稳定版
- `dorny/paths-filter@v3` - 文件变更检测
- `docker/setup-buildx-action@v3` - Docker Buildx 设置
- `docker/login-action@v3` - 容器注册表登录
- `docker/metadata-action@v5` - 元数据提取
- `docker/build-push-action@v6` - 镜像构建和推送

### 关键特性
- 支持基于文件变更的条件构建
- 使用环境变量管理敏感信息
- 支持手动触发（workflow_dispatch）
- 与现有 only-build.yml 工作流互补（main 分支推送 vs 其他分支构建）

## 状态

已完成 - 完成时间：2024年当前时间

核心工作流文件已创建并通过语法验证。所有必需的功能都已实现，包括条件构建、阿里云容器镜像服务集成和使用最新稳定版本的 GitHub Actions。