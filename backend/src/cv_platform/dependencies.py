from functools import lru_cache

from .core.container import ApplicationContainer, build_container


@lru_cache
def get_container() -> ApplicationContainer:
    return build_container()

