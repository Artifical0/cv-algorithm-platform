from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import MetaData, engine_from_config, pool
from sqlalchemy.engine import URL


config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Migrations are intentionally explicit, like Flyway version scripts. ORM metadata can
# be assigned here when the PostgreSQL repository adapters are introduced.
target_metadata = MetaData()


def database_url() -> str:
    value = os.getenv("CV_PLATFORM_DATABASE_URL") or os.getenv("DATABASE_URL")
    if value:
        return value
    password = os.getenv("CV_PLATFORM_POSTGRES_PASSWORD")
    if password:
        return URL.create(
            "postgresql+psycopg",
            username=os.getenv("CV_PLATFORM_POSTGRES_USER", "cv_platform"),
            password=password,
            host=os.getenv("CV_PLATFORM_POSTGRES_HOST", "localhost"),
            port=int(os.getenv("CV_PLATFORM_POSTGRES_PORT", "5432")),
            database=os.getenv("CV_PLATFORM_POSTGRES_DB", "cv_platform"),
        ).render_as_string(hide_password=False)
    if context.is_offline_mode():
        return "postgresql+psycopg://offline:offline@localhost/cv_platform"
    raise RuntimeError(
        "Set CV_PLATFORM_DATABASE_URL, DATABASE_URL, or CV_PLATFORM_POSTGRES_PASSWORD "
        "for online migrations"
    )


def run_migrations_offline() -> None:
    context.configure(
        url=database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        transaction_per_migration=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section) or {}
    # This is a plain section dictionary, so URL-encoded percent signs remain unchanged.
    section["sqlalchemy.url"] = database_url()
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            transaction_per_migration=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
