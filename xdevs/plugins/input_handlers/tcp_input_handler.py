from __future__ import annotations
import queue
import threading
from typing import Any
from xdevs.plugins.util.socket_server import SocketServer
from xdevs.rt_sim.input_handler import InputHandler


class TCPInputHandler(InputHandler):  # TODO cambiar a SocketServerInputHandler (más generico que TCP, abre la puerta a SocketClientInputHandler)
    def __init__(self, **kwargs):
        """
        TCPInputHandler is a socket server. The server receives the clients messages and inject them to the system as
        ingoing events.

        Default format for client messages must be: Port,msg.  If a different format is chosen a new function to parser
        them must be given (event_parser).

        Be aware that all the clients must use the same format. It is recommended that to implement multiple clients
        with different message formats, create as many TCPInputHandlers as formats.

        :param str host: is the IP of the network interface on which  the server is listening for incoming connections.
            Interesting values are '127.0.0.1' for the loopback interface (LocalHost) or '0.0.0.0' for listening to all
            interfaces. Default is 'LocalHost'
        :param int port: is the port in which the server is listening
        :param Callable[any, [str,str]] event_parser: A function that converts the messages of each client (any) to the
            correct ingoing event format required by the system (str, str). First str must be the port name for the
            ingoing event and the second one what is going to be injected in that port.
        """

        kwargs['event_parser'] = kwargs.get('event_parser', lambda x: x.decode().split(','))
        super().__init__(**kwargs)

        # process socket server configuration
        self.server_address: tuple[Any, ...] = kwargs.get('address')
        if self.server_address is None:
            host: str = kwargs.get('host', 'LocalHost')
            port: int = kwargs.get('port')
            if port is None:
                raise ValueError('TCP port is mandatory')
            self.server_address = (host, port)
        self.server_socket = kwargs.get('socket')
        self.max_clients: int | None = kwargs.get('max_clients')

        # create socket server to handle the communications
        self.server = SocketServer(self.server_address, self.server_socket, self.max_clients)
        self.server_thread: threading.Thread = threading.Thread(target=self.server.start, daemon=True)

    def initialize(self):
        self.server_thread.start()

    def run(self):
        """It just forwards messages from the server queue to the RT manager's queue."""
        while True:
            event = self.server.input_queue.get()
            self.push_event(event)


if __name__ == '__main__':
    input_queue = queue.SimpleQueue()

    TCP = TCPInputHandler(port=4321, queue=input_queue)
    TCP.initialize()
    TCP.run()
