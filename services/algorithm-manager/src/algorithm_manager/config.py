from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ALGORITHM_MANAGER_", env_file=".env")

    app_name: str = "CV Algorithm Manager"
    docker_network: str = "cv-algorithm-platform_default"
    host_data_root: Path = Path("/srv/cv-platform/data")
    host_model_root: Path = Path("/srv/cv-platform/models")
    package_root: Path = Path("/packages")
    build_network: str = "bridge"
    health_timeout_seconds: float = 60
    idle_timeout_seconds: int = 1800
    health_monitor_seconds: int = Field(default=15, ge=5, le=300)
    health_failure_threshold: int = Field(default=3, ge=1, le=20)


@lru_cache
def get_settings() -> Settings:
    return Settings()
