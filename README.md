# CV Algorithm Platform

多算法计算机视觉托管、运行、对比与结果可视化平台。

本目录是多算法平台的独立开发项目。现有 `fasterrcnn_trainer-master` 作为原型和迁移来源保留，不在原目录继续堆叠新平台功能。

## 产品文档

- [多算法 CV 可视化平台 PRD](docs/PRD-多算法CV可视化平台.md)
- [第一轮开发说明](docs/ROUND-1-DEVELOPMENT.md)
- [第二轮开发说明](docs/ROUND-2-DEVELOPMENT.md)
- [第三至第五轮开发说明](docs/ROUND-3-TO-5-DEVELOPMENT.md)
- [PRD 功能覆盖矩阵](docs/FEATURE-COVERAGE.md)
- [本地服务器部署说明](docs/SERVER-DEPLOYMENT.md)

## 目录结构

```text
cv-algorithm-platform/
├── frontend/                    # Vue 3 前端
├── backend/                     # FastAPI 平台 API
├── services/
│   └── algorithm-manager/       # Docker 容器生命周期与资源管理
├── packages/
│   └── algorithm-sdk/           # 算法协议、Schema 与容器服务 SDK
├── runtimes/
│   ├── pytorch/                 # PyTorch 受控基础运行时
│   ├── paddle/                  # PaddlePaddle 受控基础运行时
│   └── onnx/                    # ONNX Runtime 受控基础运行时
├── examples/
│   ├── faster-rcnn/             # 第一个迁移算法
│   └── yolo/                    # 第二个验证算法
├── infra/
│   └── docker/                  # 本地服务器与基础服务部署
├── database/                    # PostgreSQL Alembic 版本迁移
├── docs/                        # PRD、架构和接口文档
└── tests/                       # 跨服务协议与集成测试
```

## 已完成能力

- MVP：安全算法导入、独立 Docker 容器、图片推理、统一结果、多算法对比。
- V1：五类 CV 结果、版本治理、项目级 RBAC、SSE、结果归档、GPU/LRU 治理。
- V2：视频/摄像头/RTSP、多 GPU/多节点、DAG、BentoML/KServe、灰度与自动扩缩容。
- PostgreSQL 首版表结构与 Alembic 版本迁移已就绪；默认运行仍不创建数据库。

详见 [功能覆盖矩阵](docs/FEATURE-COVERAGE.md) 与 [服务器部署说明](docs/SERVER-DEPLOYMENT.md)。

## 原 MVP 开发顺序

1. 定义算法 `manifest`、容器 API 和统一 Result Schema。
2. 创建 Algorithm SDK 和协议测试。
3. 将 Faster R-CNN 推理拆成第一个独立算法容器。
4. 实现 FastAPI 任务中心和 Algorithm Manager。
5. 接入 YOLO，验证不同依赖环境隔离。
6. 实现同一图片的多算法并排对比。

## 开发原则

- 主平台不直接导入或执行算法 Python 代码。
- 普通用户不能上传任意 Dockerfile。
- Algorithm Manager 是唯一允许访问 Docker Engine API 的服务。
- 所有算法容器统一实现 `/health`、`/metadata` 和 `/predict`。
- 所有结果必须通过统一 Schema 校验后才能进入结果中心。
- MVP 使用单机 Docker，不引入 Kubernetes。

## 当前本地预览

安装依赖后分别启动后端和前端，具体命令见[第一轮开发说明](docs/ROUND-1-DEVELOPMENT.md)。也可以构建开发镜像：

```powershell
docker compose up --build
```

然后访问 `http://localhost:8080`。

首次部署必须在 `.env` 设置强管理员密码：

```text
CV_PLATFORM_ADMIN_USERNAME=admin
CV_PLATFORM_ADMIN_PASSWORD=<至少 12 位强密码>
```

准备服务器目录和验证项目：

```powershell
.\scripts\prepare-server.ps1
.\scripts\verify.ps1
```

当前运行时尚未启用数据库仓储。算法注册、任务、结果、会话和审计位于内存；图片、模型与算法包使用受控文件目录；Algorithm Manager 重启后会通过 Docker 标签恢复其管理的容器索引。

服务器持久化阶段已准备 PostgreSQL 迁移，详见 [数据库迁移说明](database/README.md)。它支持版本查询、升级、回滚和离线 SQL 导出，且不会在本地自动建库。
