# 第一轮开发说明

## 本轮目标

第一轮聚焦可维护的工程骨架和稳定协议，不接入 Docker Engine、Redis、数据库或真实模型。

已实现：

- Algorithm SDK 独立 Python 包。
- `manifest.yaml` 严格校验和运行参数校验。
- `/health`、`/metadata`、`/predict` 容器协议。
- 目标检测统一 Result Schema。
- Faster R-CNN、YOLO 两个模拟算法服务及契约测试。
- 分层 FastAPI 后端和可替换内存仓储。
- 算法列表、算法详情、任务创建和任务查询 API。
- Vue 3 + TypeScript + Vite 前端。
- API、类型、组合函数、布局、页面和业务组件分层。
- 工作台、算法中心、任务中心首轮界面。

## 后端结构约束

每个业务模块使用以下结构：

```text
modules/<module>/
├── api/              # HTTP 路由和请求响应 DTO
├── application/      # 用例编排和业务服务
├── domain/           # 实体与仓储协议
└── infrastructure/   # 数据库、内存、外部服务适配器
```

依赖方向为：

```text
api → application → domain
                 ↑
        infrastructure
```

路由不得直接操作数据库或 Docker。业务实体不得依赖 FastAPI。

## 前端结构约束

```text
src/
├── api/              # HTTP 客户端
├── components/       # 可复用展示和业务组件
├── composables/      # 页面状态和异步逻辑
├── router/           # 路由配置
├── styles/           # 全局设计系统
├── types/            # API 和领域类型
└── views/            # 页面编排
```

页面不直接调用 `fetch`；必须通过 `api` 和 `composables`。公共类型不在组件内重复定义。

## 本地启动

建议安装 `uv` 后在项目根目录执行：

```bash
uv sync --all-packages --all-extras
uv run --package cv-platform-backend uvicorn cv_platform.main:app --reload --port 8000
```

前端：

```bash
cd frontend
npm install
npm run dev
```

浏览器访问 `http://localhost:5173`，Vite 会把 `/api` 代理到 `http://localhost:8000`。

## 测试命令

```bash
uv run --package cv-algorithm-sdk pytest packages/algorithm-sdk/tests
uv run --package cv-platform-backend pytest backend/tests
uv run --package cv-platform-backend pytest tests

cd frontend
npm test
npm run build
```

### 当前本机验证记录

- Python AST 解析：通过。
- JSON 配置解析：通过。
- 前端依赖边界检查：通过，页面和组件未直接调用 `fetch`。
- 后端领域边界检查：通过，领域层未依赖 FastAPI、数据库或 Docker。
- Python/Node 依赖安装：因当前网络下载速度极低而未完成。
- pytest、Vitest、TypeScript 检查及 Vite 构建：等待依赖安装后执行。

## 后续轮次边界（已在第三至第五轮完成）

1. 将 Faster R-CNN 真实推理代码迁移进示例算法容器。
2. 加入 Algorithm Manager 的接口与 Docker Engine 适配器。
3. 暂时保留内存仓储，数据库推迟到服务器部署阶段。
4. 加入资源上传和受控文件存储。
5. 先完成同步推理闭环，再在服务器阶段接入 Redis/Celery。
