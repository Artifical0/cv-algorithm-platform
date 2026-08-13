# Development Roadmap

## Phase 1: Protocol First

状态：已完成。

- 定义 `manifest.yaml` Schema。
- 定义 `/health`、`/metadata`、`/predict` 协议。
- 定义目标检测 Result Schema。
- 建立协议校验和契约测试。

完成标准：两个模拟算法服务能够通过同一套契约测试。

## Phase 2: First Algorithm Container

状态：已完成代码迁移；真实权重联调需服务器模型文件。

- 从旧项目迁移 Faster R-CNN 推理代码。
- 算法容器独立加载模型与权重。
- 返回标准目标检测结果。
- 支持 CPU 与 CUDA 运行配置。

完成标准：主平台不导入 Faster R-CNN 源码，通过 HTTP 完成推理。

## Phase 3: Platform Core

状态：已完成本地无数据库实现。

- FastAPI 算法、资源、任务和结果模块。
- Algorithm Manager 启动、检查、复用和停止容器。
- 开发阶段使用内存仓储与 Docker 标签恢复，不依赖数据库。
- 通过异步任务队列与 HTTP 算法协议完成端到端推理闭环。

完成标准：图片上传后能够调用 Faster R-CNN 容器并查看结果。

## Phase 3.5: Server Persistence

状态：按用户要求后移，不在本地创建数据库。

- 服务器部署时引入 PostgreSQL，替换算法、任务与结果内存仓储。
- 引入对象存储保存图片、权重和结果文件。
- 引入 Redis/Celery 异步任务、重试和队列隔离。

完成标准：服务重启不丢失平台业务数据，长任务不占用 API 请求连接。

## Phase 4: Multi-Algorithm Proof

状态：已完成代码实现；真实模型联调需服务器 Docker/GPU 环境。

- 接入 YOLO 算法容器。
- 根据算法 manifest 动态生成参数表单。
- 同一图片并行创建多个算法任务。
- 实现检测结果并排对比。

完成标准：Faster R-CNN 和 YOLO 使用不同镜像，对同一图片输出统一结果并在同一页面比较。

## Phase 5: Algorithm Import

状态：已完成受控 ZIP、模板构建、日志和三接口协议验收实现。

- 受控 ZIP 上传和安全解压。
- manifest 校验、构建队列和日志。
- BentoML 或受控运行时模板构建。
- 测试容器与协议验收。

完成标准：标准示例算法包可以从前端导入并注册为可用版本。

## Phase 6: V1 Productization

状态：已完成本地无数据库实现。

- 五类结果协议与渲染器。
- 版本启停、回滚、删除保护和结果批量归档。
- SSE、任务筛选、取消和重试。
- 用户/角色、项目 owner/editor/viewer 权限与跨项目数据隔离。
- GPU 显存估算、LRU 路由和持续健康监控。

## Phase 7: V2 Orchestration

状态：已完成代码实现；真实摄像头、RTSP、多 GPU 和多节点联调需目标服务器环境。

- 视频上传、摄像头/RTSP、OpenCV 抽帧与逐帧推理。
- 多 GPU 具体索引选择、多 Manager 节点调度与真实副本协调。
- 串行/并行 DAG 工作流、取消与失败传播。
- BentoML class-based ASGI 包装产物、KServe InferenceService 产物。
- 灰度权重、运行指标、自动扩缩容与空闲冷却。

完成标准：在具备 Docker/GPU/摄像头或 RTSP 的服务器上执行部署验收清单。
