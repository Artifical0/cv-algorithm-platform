# Algorithm Manager

该服务是主平台与 Docker Engine 之间唯一的控制边界。第二轮使用内存仓储，服务重启后实例记录会通过 Docker 标签重新发现，不依赖数据库。

计划职责：

- 创建、启动、检查、复用、停止和移除算法容器。
- 分配 CPU、内存和 GPU 资源。
- 执行容器健康检查和空闲回收。
- 将 Docker 错误转换为平台业务错误。
- 通过 `cv.platform.managed=true` 标签限定可管理容器范围。

主平台 API、算法容器和普通任务 Worker 均不得直接访问 Docker Socket。

开发启动：

```powershell
uv run --project services/algorithm-manager uvicorn algorithm_manager.main:app --port 8010 --reload
```

环境变量均以 `ALGORITHM_MANAGER_` 开头。生产环境应使用受限 Docker Socket 代理；直接挂载 `/var/run/docker.sock` 仅适合可信的单机部署。
