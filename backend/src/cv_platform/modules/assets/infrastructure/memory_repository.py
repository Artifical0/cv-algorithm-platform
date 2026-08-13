from threading import RLock
from uuid import UUID

from ..domain.entities import ImageAsset


class InMemoryAssetRepository:
    def __init__(self) -> None:
        self._items: dict[UUID, ImageAsset] = {}
        self._by_sha256: dict[str, UUID] = {}
        self._lock = RLock()

    def add(self, asset: ImageAsset) -> None:
        with self._lock:
            self._items[asset.id] = asset
            self._by_sha256[asset.sha256] = asset.id

    def list(self) -> list[ImageAsset]:
        with self._lock:
            return sorted(self._items.values(), key=lambda item: item.created_at, reverse=True)

    def get(self, asset_id: UUID) -> ImageAsset | None:
        with self._lock:
            return self._items.get(asset_id)

    def find_by_sha256(self, sha256: str) -> ImageAsset | None:
        with self._lock:
            asset_id = self._by_sha256.get(sha256)
            return self._items.get(asset_id) if asset_id else None
