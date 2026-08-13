from typing import Protocol
from uuid import UUID

from .entities import ImageAsset


class AssetRepository(Protocol):
    def add(self, asset: ImageAsset) -> None: ...

    def list(self) -> list[ImageAsset]: ...

    def get(self, asset_id: UUID) -> ImageAsset | None: ...

    def find_by_sha256(self, sha256: str) -> ImageAsset | None: ...
