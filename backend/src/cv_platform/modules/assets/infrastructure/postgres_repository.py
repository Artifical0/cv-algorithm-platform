from __future__ import annotations

from uuid import UUID

from ....core.database import Database
from ..domain.entities import ImageAsset


class PostgresAssetRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    @staticmethod
    def _from_row(row: dict[str, object]) -> ImageAsset:
        return ImageAsset(
            id=row["id"],
            original_name=str(row["original_name"]),
            storage_key=str(row["storage_key"]),
            algorithm_uri=str(row["algorithm_uri"]),
            sha256=str(row["sha256"]),
            media_type=str(row["media_type"]),
            width=int(row["width"]),
            height=int(row["height"]),
            size_bytes=int(row["size_bytes"]),
            created_at=row["created_at"],
            owner_id=str(row["owner_label"]),
            project_id=row["project_id"],
        )

    def add(self, asset: ImageAsset) -> None:
        with self._database.connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO image_assets (
                    id, project_id, owner_id, owner_label, original_name, storage_key,
                    algorithm_uri, sha256, media_type, width, height, size_bytes, created_at
                ) VALUES (%s, %s, NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    asset.id,
                    asset.project_id,
                    asset.owner_id,
                    asset.original_name,
                    asset.storage_key,
                    asset.algorithm_uri,
                    asset.sha256,
                    asset.media_type,
                    asset.width,
                    asset.height,
                    asset.size_bytes,
                    asset.created_at,
                ),
            )

    def list(self) -> list[ImageAsset]:
        with self._database.connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM image_assets WHERE deleted_at IS NULL ORDER BY created_at DESC"
            )
            return [self._from_row(row) for row in cursor.fetchall()]

    def get(self, asset_id: UUID) -> ImageAsset | None:
        with self._database.connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM image_assets WHERE id = %s AND deleted_at IS NULL",
                (asset_id,),
            )
            row = cursor.fetchone()
            return self._from_row(row) if row else None

    def find_by_sha256(self, sha256: str) -> ImageAsset | None:
        with self._database.connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM image_assets
                WHERE sha256 = %s AND deleted_at IS NULL
                ORDER BY created_at DESC LIMIT 1
                """,
                (sha256,),
            )
            row = cursor.fetchone()
            return self._from_row(row) if row else None
