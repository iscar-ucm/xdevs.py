from __future__ import annotations
import pkg_resources
from typing import ClassVar, Type
from xdevs.models import Atomic


class Wrappers:
    _plugins: ClassVar[dict[str, Type[Atomic]]] = {
        ep.name: ep.load() for ep in pkg_resources.iter_entry_points('xdevs.plugins.wrappers')
    }

    @staticmethod
    def add_plugin(name: str, plugin: Type[Atomic]):
        if name in Wrappers._plugins:
            raise ValueError(f'xDEVS wrapper plugin with name "{name}" already exists')
        Wrappers._plugins[name] = plugin

    @staticmethod
    def get_wrapper(name: str) -> Type[Atomic]:
        if name not in Wrappers._plugins:
            raise ValueError(f'xDEVS wrapper plugin with name "{name}" not found')
        return Wrappers._plugins[name]
