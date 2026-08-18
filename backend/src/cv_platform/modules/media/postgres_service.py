from __future__ import annotations

from uuid import UUID

from ...core.database import Database
from ...core.errors import ApplicationError
from ...core.project_context import DEFAULT_PROJECT_ID
from .domain import MediaSource, MediaSourceType
from .service import InMemoryMediaSourceService


class PostgresMediaSourceService:
    def __init__(self, database: Database) -> None:
        self._database = database

    @staticmethod
    def _from_row(row: dict[str, object]) -> MediaSource:
        return MediaSource(
            id=row["id"],
            name=str(row["name"]),
            source_type=MediaSourceType(str(row["source_type"])),
            uri=str(row["uri"]),
            enabled=bool(row["enabled"]),
            created_at=row["created_at"],
            owner_id=str(row["owner_label"]),
            project_id=row["project_id"],
        )

    def create(
        self,
        name: str,
        source_type: MediaSourceType,
        uri: str,
        project_id: UUID = DEFAULT_PROJECT_ID,
        owner_id: str = "local-admin",
    ) -> MediaSource:
        InMemoryMediaSourceService._validate_uri(source_type, uri)
        source = MediaSource.create(name.strip(), source_type, uri, project_id, owner_id)
        with self._database.connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO media_sources (
                    id, project_id, owner_id, owner_label, name,
                    source_type, uri, enabled, created_at
                ) VALUES (%s, %s, NULL, %s, %s, %s, %s, %s, %s)
                """,
                (
                    source.id,
                    source.project_id,
                    source.owner_id,
                    source.name,
                    source.source_type.value,
                    source.uri,
                    source.enabled,
                    source.created_at,
                ),
            )
        return source

    def list(self, project_id: UUID | None = None) -> list[MediaSource]:
        with self._database.connect() as connection, connection.cursor() as cursor:
            if project_id is None:
                cursor.execute("SELECT * FROM media_sources ORDER BY created_at DESC")
            else:
                cursor.execute(
                    "SELECT * FROM media_sources WHERE project_id = %s ORDER BY created_at DESC",
                    (project_id,),
                )
            return [self._from_row(row) for row in cursor.fetchall()]

    def get(self, source_id: UUID, project_id: UUID | None = None) -> MediaSource:
        with self._database.connect() as connection, connection.cursor() as cursor:
            if project_id is None:
                cursor.execute("SELECT * FROM media_sources WHERE id = %s", (source_id,))
            else:
                cursor.execute(
                    "SELECT * FROM media_sources WHERE id = %s AND project_id = %s",
                    (source_id, project_id),
                )
            row = cursor.fetchone()
        if row is None:
            raise ApplicationError("MEDIA_SOURCE_NOT_FOUND", "媒体源不存在", 404)
        return self._from_row(row)

    def delete(self, source_id: UUID, project_id: UUID | None = None) -> None:
        self.get(source_id, project_id)
        with self._database.connect() as connection, connection.cursor() as cursor:
            cursor.execute("DELETE FROM media_sources WHERE id = %s", (source_id,))
