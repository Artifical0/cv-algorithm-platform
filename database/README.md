# PostgreSQL 数据库迁移

本目录提供类似 Flyway 的版本化数据库迁移。迁移按 `revision` 严格排序，已执行版本记录在数据库的 `alembic_version` 表中。叠加 `compose.database.yaml` 后，Backend 会使用 PostgreSQL 业务仓储；只运行基础 `compose.yaml` 时仍可使用内存模式开发。

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

`compose.database.yaml` 会设置 `CV_PLATFORM_PERSISTENCE_BACKEND=postgres`。直接运行 Backend 时也必须显式设置该变量，否则默认保留内存模式。

首次初始化会幂等创建 `.env` 中配置的管理员和默认项目。管理员一旦写入数据库，后续只修改 `.env` 密码不会覆盖已有密码；生产环境密码轮换应通过专用管理流程执行。

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
