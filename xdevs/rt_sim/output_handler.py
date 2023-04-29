from __future__ import annotations
import queue
from abc import ABC, abstractmethod
import sys
from typing import Any, Callable, ClassVar, Type

import pkg_resources


class OutputHandler(ABC):
    def __init__(self, **kwargs):
        """
        Handler interface for ejecting internal events from the system.

        TODO documentation
        """
        self.queue = queue.SimpleQueue()
        self.event_parser: Callable[[str, str], Any] | None = kwargs.get('event_parser')
        self.msg_parsers: dict[str, Callable[[Any], str]] = kwargs.get('msg_parsers', dict())

    def initialize(self):
        """Performs any task before calling the run method. It is implementation-specific. By default, it is empty."""
        pass

    def exit(self):
        """Performs any task before calling the run method. It is implementation-specific. By default, it is empty."""
        pass

    @abstractmethod
    def run(self):
        """Execution of the output handler. It is implementation-specific"""
        pass

    def pop_event(self) -> Any:
        """Parsers the outgoing event to the desire implementation."""
        while True:
            port, msg = self.pop_msg()
            try:
                event = self.event_parser(port, msg)
            except Exception:
                print(f'error parsing output event ("{port}","{msg}"). Event will be ignored', file=sys.stderr)
                continue
            return event

    def pop_msg(self) -> tuple[str, str]:
        """Looks in the queue for outgoing events and parser the output msg."""
        while True:
            port, msg = self.queue.get()
            try:
                msg = self.msg_parsers.get(port, lambda x: str(x))(msg)
            except Exception:
                print(f'error parsing output msg ("{msg}"). Message will be ignored', file=sys.stderr)
                continue
            return port, msg

class OutputHandlers:
    _plugins: ClassVar[dict[str, Type[OutputHandler]]] = {
        ep.name: ep.load() for ep in pkg_resources.iter_entry_points('xdevs.plugins.output_handlers')
    }

    @staticmethod
    def add_plugin(name: str, plugin: Type[OutputHandler]):
        """
        Registers a custom output handler to the plugin system.

        :param name: name used to identify the custom input handler. It must be unique.
        :param plugin: custom input handler type. Note that it must not be an object, just the class.
        """
        if name in OutputHandlers._plugins:
            raise ValueError('xDEVS output_handler plugin with name "{}" already exists'.format(name))
        OutputHandlers._plugins[name] = plugin

    @staticmethod
    def create_output_handler(name: str, **kwargs) -> OutputHandler:
        """

        Creates a new output handler. Note that this is done by the real-time manager.
        Users do not directly create output handlers using this method.

        :param name: unique ID of the output handler to be created.
        :param kwargs: any additional configuration parameter needed for creating the output handler.
        :return: an instance of the OutputHandler class.
        """
        if name not in OutputHandlers._plugins:
            raise ValueError('xDEVS output_handler plugin with name "{}" not found'.format(name))
        return OutputHandlers._plugins[name](**kwargs)
