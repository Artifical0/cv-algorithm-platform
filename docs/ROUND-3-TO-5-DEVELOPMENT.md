# 第三至第五轮开发说明

## 第三轮：资源、任务与结果

- 安全图片上传、内容解码校验和 SHA-256 去重。
- 受控本地文件存储和只读算法容器挂载。
- 进程内异步推理队列、完整任务状态机、取消、重试和查询过滤。
- Algorithm Manager 按需启动算法容器，HTTP 调用 `/predict`。
- Result Schema 验证后才进入正式任务结果。
- 前端动态参数、任务轮询和检测结果 Canvas。

## 第四轮：多算法与通用结果

- Faster R-CNN 与 Ultralytics YOLO 独立镜像。
- 同图多算法并行任务与并排对比。
- 检测、分类、分割、OCR、姿态五种统一 Result Schema。
- 前端按结果类型自动选择渲染器。

## 第五轮：导入与治理

- ZIP 算法包安全校验、manifest 唯一性和 SDK 注入。
- 受控 Dockerfile 模板，不接受用户 Dockerfile。
- 异步镜像构建、顺序日志和临时容器协议验收。
- 算法版本启停、任务引用删除保护和可选镜像删除。
- 非 root、只读根、CPU/内存/PID/GPU、cap drop 和 internal network。
- 容器空闲回收、GPU 状态、容器日志、审计日志和限流。
- 环境变量单管理员认证与 HttpOnly 会话 Cookie。

## 本地异步策略

当前使用 `ThreadPoolExecutor` 实现推理和构建队列，满足 API 立即返回及状态可追踪要求。服务器持久化阶段将 `TaskQueue` 和 Build Queue 适配器替换为 Redis/Celery，无需修改领域实体和 HTTP API。

## 算法包最低结构

```text
algorithm-package.zip
├── manifest.yaml
├── service.py
├── algorithm.py             # 可选
├── requirements.txt         # 可选
├── test/
│   └── sample.jpg           # 发布前真实 predict 验收
└── weights/                 # 可选
```

禁止包含自定义 Dockerfile、绝对路径、`..`、符号链接和设备文件。

## 验证

运行：

```powershell
.\scripts\verify.ps1
```

该脚本始终执行语法、配置、架构边界和无数据库依赖检查；安装 pytest 和前端依赖后，还会运行 Python 测试、Vitest、TypeScript 和 Vite 构建。
