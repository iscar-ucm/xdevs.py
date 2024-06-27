import queue
import sys
from abc import ABC, abstractmethod
from typing import Callable, Any


class Connector:
    def __init__(self, connections: dict[str, str]):
        """
        Function to connect ports correctly (using MQTT protocol)

        :param connections: dict[key: str, value: str]. Where the key is the port I am connecting to (via MQTT) and the value is the port of my coupled.
        """
        self.connections: dict[str, str] = connections

    def input_handler(self, port: str):
        if self.connections is not None:
            value = self.connections.get(port)
            if value is not None:
                return value
        return port


class InputHandler(ABC):
    def __init__(self, *args, **kwargs):
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

        self.connections: dict[str, str] = kwargs.get('connections', dict())
        self.connector = Connector(connections=self.connections)

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
        self.push_msg(port, msg)

    def push_msg(self, port: str, msg: str):
        """Parses the message as the proper object and pushes it to the queue."""
        try:
            # if parser is not defined, we forward the message as is (i.e., in string format)
            msg = self.msg_parsers.get(port, lambda x: x)(msg)
        except Exception as e:
            # if an exception is triggered while parsing the message, we ignore it
            print(f'error parsing input msg ("{msg}") in port {port}: {e}. Message will be ignored', file=sys.stderr)
            return
        self.queue.put((port, msg))


class OutputHandler(ABC):
    def __init__(self, *args, **kwargs):
        """
        Handler interface for ejecting internal events from the system.

        :param queue.SimpleQueue() queue: is the queue where all the desired events to be ejected are put.
        :param Callable[[str, str], Any] event_parser: event parser function. It transforms incoming tuples
            (port, message) into events. Note that both are represented as strings.
        :param dict[str, Callable[[Any], str]] msg_parser: message parsers. Keys are port names, and values are
            functions that take a string and returns an object of the corresponding port type. If a parser is not
            defined, the output handler assumes that the port type is str and forward the message as is. By default, all
            the ports are assumed to accept str objects.

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
        """Waits until it receives an outgoing event and parses it with the desired format."""
        while True:
            port, msg = self.pop_msg()
            # print(f'POP_EVENT: recibo port = {port} y msg = {msg}')
            try:
                event = self.event_parser(port, msg)
            except Exception as e:
                print(f'error parsing output event ("{port}","{msg}"): {e}. Event will be ignored', file=sys.stderr)
                continue
            return event

    def pop_msg(self) -> tuple[str, str]:
        """Waits until it receives an outgoing message and returns the port and message in string format."""
        while True:
            port, msg = self.queue.get()
            # print(f'POP_MSG: recibo port = {port} y msg = {msg}')
            try:
                msg = self.msg_parsers.get(port, lambda x: str(x))(msg)
            except Exception as e:
                print(f'error parsing output msg ("{msg}"): {e}. Message will be ignored', file=sys.stderr)
                continue
            return port, msg
