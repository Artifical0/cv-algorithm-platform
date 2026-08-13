# 第二轮开发说明

## 本轮目标

第二轮保持无数据库架构，完成算法容器生命周期控制，并把旧项目 Faster R-CNN 推理迁入独立容器。平台业务状态继续通过仓储接口隔离，后续可直接替换为 PostgreSQL 实现。

## 已实现

- 独立 `Algorithm Manager` FastAPI 服务。
- Docker Engine 适配器，支持创建、启动、健康检查、复用、停止和删除。
- 容器名称白名单与 `cv.platform.managed=true` 标签边界。
- Manager 重启后通过 Docker 标签恢复内存实例索引。
- 同一算法版本的并发启动锁与幂等复用。
- 主后端 `instances` 模块和 Algorithm Manager HTTP 网关。
- `GET /api/v1/instances`。
- `POST /api/v1/algorithms/{algorithm_id}/start`。
- `POST /api/v1/instances/{instance_id}/stop`。
- `DELETE /api/v1/instances/{instance_id}`。
- 前端运行实例页面，可启动、复用、停止和删除算法容器。
- Faster R-CNN 真实权重加载、图片预处理、推理、阈值过滤和统一结果转换。
- 兼容旧项目 `(losses, detections)` 返回值与配置组装方式。

## 无数据库边界

当前算法、任务和运行实例均不写入数据库：

- 平台 API 重启后，内置算法由 seed 重新注册，并根据算法 key 和版本恢复稳定 UUID。
- Algorithm Manager 的内存记录会清空，但受管 Docker 容器会通过标签重新发现。
- 任务数据重启后会丢失，当前阶段仅用于开发验证。
- 算法容器通过受控只读目录访问图片和模型，不写入数据库。

服务器部署阶段再加入 PostgreSQL、对象存储和 Redis/Celery，不需要让当前领域层依赖这些基础设施。

## 构建和启动

先准备旧项目训练生成的权重，例如放到服务器：

```text
/srv/cv-platform/models/faster-rcnn-resnet50/
├── model.pth
└── model-config.yaml
```

构建算法镜像和平台镜像：

```powershell
docker compose --profile algorithm-images build faster-rcnn
docker compose build algorithm-manager backend frontend
```

启动平台：

```powershell
docker compose up -d algorithm-manager backend frontend
```

真实算法容器由 Algorithm Manager 按需创建，不应手工 `compose up faster-rcnn`。Manager 只允许挂载其环境变量配置的两个宿主机根目录；当前代码默认算法容器内路径为：

- 权重：`/models/model.pth`
- 输入图片根目录：`/data`
- 训练配置：`/models/model-config.yaml`

默认宿主机目录及覆盖变量：

- `/srv/cv-platform/data` → `ALGORITHM_MANAGER_HOST_DATA_ROOT`
- `/srv/cv-platform/models/<algorithm-key>` → `ALGORITHM_MANAGER_HOST_MODEL_ROOT`

## Faster R-CNN 运行模式

生产默认：

```text
CV_FASTER_RCNN_MODE=torchvision
```

该模式要求配置和权重存在，缺失时容器启动失败，不会返回模拟结果。契约测试显式设置：

```text
CV_FASTER_RCNN_MODE=stub
```

stub 只用于验证统一协议，不用于生产。

`model-config.yaml` 应使用训练该权重时的原始配置，确保 `num_classes`、backbone 和 RPN/ROI 组件完全匹配；镜像内的 `/app/model-config.example.yaml` 只作为格式模板。

## 当前验证

- Python `compileall`：通过。
- `compose.yaml`、manifest 和模型配置 YAML 解析：通过。
- Algorithm Manager 无依赖领域流程：通过，覆盖创建、健康复用、停止和删除。
- 当前 Windows 环境缺少 Docker CLI，未执行真实镜像构建与容器联调。
- 当前环境未安装 FastAPI、pytest 和前端 `node_modules`，完整后端/API/前端测试待依赖安装后执行。

## 后续轮次建议（已在第三至第五轮完成）

1. 完善 GPU 不可用时的调度策略、显存配额和空闲实例回收。
2. 实现图片上传到本地受控存储，并把 `asset_uri` 传给算法容器。
3. 打通任务创建、启动容器、调用 `/predict`、保存内存结果的同步闭环。
4. 增加结果画布与检测框可视化。
5. 接入第二个真实 YOLO 容器，验证多算法隔离。
