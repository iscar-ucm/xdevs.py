from abc import ABC, abstractmethod
from typing import ClassVar, Type
import pkg_resources


class InputHandler(ABC):
    def __init__(self, **kwargs):
        """
        TODO documentation

        :param queue: Queue used to
        :param kwargs:
        """
        self.queue = kwargs.get('queue')
        if self.queue is None:
            raise ValueError('queue is mandatory')

    @abstractmethod
    def initialize(self):
        """Performs any task before calling the run method. It is implementation-specific"""
        pass

    @abstractmethod
    def exit(self):
        """Performs any task after the run method. It is implementation-specific"""
        pass

    @abstractmethod
    def run(self):
        """Execution of the input handler. It is implementation-specific"""
        pass


class InputHandlers:
    _plugins: ClassVar[dict[str, Type[InputHandler]]] = {
        ep.name: ep.load() for ep in pkg_resources.iter_entry_points('xdevs.plugins.input_handlers')
    }

    @staticmethod
    def add_plugin(name: str, plugin: Type[InputHandler]):
        """
        Registers a custom input handler to the plugin system.

        :param name: name used to identify the custom input handler. It must be unique.
        :param plugin: custom input handler type. Note that it must not be an object, just the class.
        """
        if name in InputHandlers._plugins:
            raise ValueError('xDEVS input_handler plugin with name "{}" already exists'.format(name))
        InputHandlers._plugins[name] = plugin

    @staticmethod
    def create_input_handler(name: str, **kwargs) -> InputHandler:
        """
        Creates a new input handler. Note that this is done by the real-time manager.
        Users do not directly create input handlers using this method.

        :param name: unique ID of the input handler to be created.
        :param kwargs: any additional configuration parameter needed for creating the input handler.
        :return: an instance of the InputHandler class.
        """
        if name not in InputHandlers._plugins:
            raise ValueError('xDEVS input_handler plugin with name "{}" not found'.format(name))
        return InputHandlers._plugins[name](**kwargs)
