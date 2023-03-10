from abc import ABC, abstractmethod
from typing import ClassVar, Type

import pkg_resources


class InputHandler(ABC):
    def __init__(self, **kwargs):
        self.queue = kwargs.get('queue')
        if self.queue is None:
            raise ValueError('queue is mandatory')

    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def exit(self):
        pass

    @abstractmethod
    def run(self):
        "Execution of the InputHandler"
        pass


class InputHandlers:
    _plugins: ClassVar[dict[str, Type[InputHandler]]] = {
        ep.name: ep.load() for ep in pkg_resources.iter_entry_points('xdevs.plugins.input_handlers')
    }

    @staticmethod
    def add_plugin(name: str, plugin: Type[InputHandler]):
        if name in InputHandlers._plugins:
            raise ValueError('xDEVS input_handler plugin with name "{}" already exists'.format(name))
        InputHandlers._plugins[name] = plugin

    @staticmethod
    def create_input_handler(name: str, **kwargs) -> InputHandler:
        if name not in InputHandlers._plugins:
            raise ValueError('xDEVS input_handler plugin with name "{}" not found'.format(name))
        return InputHandlers._plugins[name](**kwargs)