from __future__ import annotations

import datetime
from abc import ABC, abstractmethod
from typing import ClassVar, Type, Callable, Any
import sys
import pkg_resources

from xdevs.rt_sim.mqtt_connector import Connector


class InputHandler(ABC):
    def __init__(self, **kwargs):
        """
        Handler interface for injecting external events to the system.

        :param queue: used to collect and inject all external events joining the system.
        :param Callable[[Any], tuple[str, str]] event_parser: event parser function. It transforms incoming events
            into tuples (port, message). Note that both are represented as strings. Messages need further parsing.
        :param dict[str, Callable[[str], Any]] msg_parsers: message parsers. Keys are port names, and values are
            functions that take a string and returns an object of the corresponding port type. If a parser is not
            defined, the input handler assumes that the port type is str and forward the message as is. By default, all
            the ports are assumed to accept str objects.
        """
        self.queue = kwargs.get('queue')
        if self.queue is None:
            raise ValueError('queue is mandatory')
        self.event_parser: Callable[[Any], tuple[str, str]] | None = kwargs.get('event_parser')
        self.msg_parsers: dict[str, Callable[[str], Any]] = kwargs.get('msg_parsers', dict())

        self.connections: dict[str, str] = kwargs.get('connections', None)
        self.connector = Connector(conections=self.connections)

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

    def push_event(self, event: Any):
        """Parses event as tuple port-message and pushes it to the queue."""
        try:
            port, msg = self.event_parser(event)
            # AQUI IRIA EL CONECTOR MQTT; para corregir el puerto en cuestion
            port = self.connector.input_handler(port)
        except Exception as e:
            # if an exception is triggered while parsing the event, we ignore it
            print(f'error parsing input event ("{event}"): {e}. Event will be ignored', file=sys.stderr)
            return
        #print(f'HAGO PUSH MSG DE {port},{msg}')
        self.push_msg(port, msg)

    def push_msg(self, port: str, msg: str):
        """Parses the message as the proper object and pushes it to the queue."""
        #print(f'Entro en push_msg con port ->{port}')
        try:
            # if parser is not defined, we forward the message as is (i.e., in string format)
            msg = self.msg_parsers.get(port, lambda x: x)(msg)
            #print(f'EL msg = {msg}')
        except Exception as e:
            # if an exception is triggered while parsing the message, we ignore it
            print(f'error parsing input msg ("{msg}") in port {port}: {e}. Message will be ignored', file=sys.stderr)
            return
        #print('###')
        #print(f'EVENTO ENTRA EN LA COLA EN:{datetime.datetime.time()}')
        self.queue.put((port, msg))
        #print(f'COla = {self.queue}, puse en {port}:{msg}')


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
