# PostgreSQL 数据库迁移

本目录提供类似 Flyway 的版本化数据库迁移。迁移按 `revision` 严格排序，已执行版本记录在数据库的 `alembic_version` 表中。当前应用仍默认使用内存仓储；除非显式运行数据库 Compose 配置或迁移命令，否则不会创建、连接或修改数据库。

## 目录

```text
database/
├── alembic.ini
├── requirements.txt
└── migrations/
    ├── env.py
    ├── script.py.mako
    └── versions/
        └── 20260813_0001_initial_platform_schema.py
```

首版结构覆盖用户和会话、项目成员、算法版本、构建日志、图片资源、推理任务和结果、算法对比、运行节点和容器、视频源、媒体任务、工作流、扩缩容策略与审计事件。

## 服务器首次建库

`.env` 至少设置：

```dotenv
CV_PLATFORM_POSTGRES_DB=cv_platform
CV_PLATFORM_POSTGRES_USER=cv_platform
CV_PLATFORM_POSTGRES_PASSWORD=<强随机密码>
```

启动 PostgreSQL 并自动迁移到最新版本：

```powershell
docker compose -f compose.yaml -f compose.database.yaml --profile database up -d postgres
docker compose -f compose.yaml -f compose.database.yaml --profile database run --rm database-migrator upgrade head
```

确认当前版本：

```powershell
docker compose -f compose.yaml -f compose.database.yaml --profile database run --rm database-migrator current
```

数据库准备好后启动整个平台：

```powershell
docker compose -f compose.yaml -f compose.database.yaml --profile database up -d
```

注意：迁移脚本和数据库已经就绪，但 PostgreSQL 仓储适配器尚未替换当前内存仓储。现阶段给 Backend 注入数据库地址不会改变业务数据的保存位置，后续接入仓储时无需重做表结构和版本机制。

## 不启动数据库，仅生成 SQL

安装迁移工具后，可以离线生成 PostgreSQL SQL，不连接任何数据库：

```powershell
./scripts/database.ps1 -Action install
./scripts/database.ps1 -Action sql -Revision head
```

默认输出到 `database/generated/upgrade.sql`，该目录不提交 Git。离线 SQL 适合由 DBA 审查后执行，但推荐生产环境仍由 Alembic 执行，以可靠维护版本记录。

## 连接现有 PostgreSQL

```powershell
$env:CV_PLATFORM_DATABASE_URL = 'postgresql+psycopg://cv_platform:<password>@127.0.0.1:5432/cv_platform'
./scripts/database.ps1 -Action current
./scripts/database.ps1 -Action upgrade -Revision head
```

直接使用 `CV_PLATFORM_POSTGRES_*` 分项变量时不需要手工编码密码；只有使用完整 `CV_PLATFORM_DATABASE_URL` 时，密码中的 `@`、`:`、`/`、`%` 等字符才需要 URL 编码。

## 创建下一版迁移

```powershell
./scripts/database.ps1 -Action new -Message 'add dataset tables'
```

检查新文件，手工编写 `upgrade()` 与 `downgrade()`，然后执行：

```powershell
./scripts/database.ps1 -Action history
./scripts/database.ps1 -Action upgrade -Revision head
```

禁止修改已经在任一环境执行过的迁移文件；结构变化必须创建新版本。这与 Flyway 的追加式迁移原则一致。

## 回滚

先备份，再回滚一个版本：

```powershell
./scripts/database.ps1 -Action downgrade -Revision '-1'
```

回滚到空结构会删除所有平台表，只能在确认备份可恢复后使用：

```powershell
./scripts/database.ps1 -Action downgrade -Revision base
```
