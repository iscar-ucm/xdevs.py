import pkg_resources
from typing import ClassVar
from xdevs.models import Component


class Components:
    _plugins: ClassVar[dict[str, type[Component]]] = {
        ep.name: ep.load() for ep in pkg_resources.iter_entry_points('xdevs.plugins.components')
    }

    @staticmethod
    def add_plugin(component_id: str, plugin: type[Component]):
        if component_id in Components._plugins:
            raise ValueError(f'xDEVS component plugin with name "{component_id}" already exists')
        Components._plugins[component_id] = plugin

    @staticmethod
    def create_component(component_id: str, *args, **kwargs) -> type[Component]:
        if component_id not in Components._plugins:
            raise ValueError(f'xDEVS component plugin with name "{component_id}" not found')
        return Components._plugins[component_id](*args, **kwargs)
