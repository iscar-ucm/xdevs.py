from abc import ABC, abstractmethod
from typing import ClassVar, Type, Callable, Any
import pkg_resources


class InputHandler(ABC):
    def __init__(self, **kwargs):
        """
        Handler interface for injecting external events to the system.

        :param queue: used to collect and inject all external events joining the system.
        :param event_parser: # TODO
        :param dict[str, Callable[[str], Any]] msg_parsers: message parsers. Keys are port names, and values are
            functions that take a string and returns an object of the corresponding port type. If a parser is not
            defined, the input handler assumes that the port type is str and forward the message as is. By default, all
            the ports are assumed to accept str objects.

        """
        self.queue = kwargs.get('queue')
        if self.queue is None:
            raise ValueError('queue is mandatory')

        # event_parser que va a ser para el tcp-syst una unica funcion.

        # Ver si lo pongo en la padre o especifico para cada implementación. Puede necesitarsse una función por
        # implementacion, pero se llamarán igual "event_parser".
        self.event_parser = kwargs.get('event_parser', None)

        self.msg_parsers: dict[str, Callable[[str], Any]] = kwargs.get('msg_parsers', dict())

    def initialize(self):
        """Performs any task before calling the run method. It is implementation-specific. By default, it is empty."""
        pass

    def exit(self):
        """Performs any task after the run method. It is implementation-specific. By default, it is empty."""
        pass

    @abstractmethod
    def run(self):
        """Execution of the input handler. It is implementation-specific"""
        pass

    def push_to_queue(self, port, msg):
        """Adding the port and message to the queue."""
        self.queue.put((port, msg))

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
