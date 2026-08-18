from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

import psycopg
from psycopg import Connection
from psycopg.rows import dict_row

from .config import Settings


@dataclass(frozen=True, slots=True)
class Database:
    """Small connection factory for synchronous FastAPI repository adapters."""

    conninfo: str | None
    host: str
    port: int
    dbname: str
    user: str
    password: str | None

    @classmethod
    def from_settings(cls, settings: Settings) -> "Database":
        conninfo = settings.database_url
        if conninfo and conninfo.startswith("postgresql+psycopg://"):
            conninfo = "postgresql://" + conninfo.removeprefix("postgresql+psycopg://")
        return cls(
            conninfo=conninfo,
            host=settings.postgres_host,
            port=settings.postgres_port,
            dbname=settings.postgres_db,
            user=settings.postgres_user,
            password=settings.postgres_password,
        )

    @contextmanager
    def connect(self) -> Iterator[Connection[dict[str, object]]]:
        if self.conninfo:
            connection = psycopg.connect(
                self.conninfo,
                row_factory=dict_row,
                connect_timeout=5,
            )
        else:
            if not self.password:
                raise RuntimeError("CV_PLATFORM_POSTGRES_PASSWORD is required")
            connection = psycopg.connect(
                host=self.host,
                port=self.port,
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                row_factory=dict_row,
                connect_timeout=5,
            )
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def is_healthy(self) -> bool:
        try:
            with self.connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    return cursor.fetchone() is not None
        except psycopg.Error:
            return False
