from __future__ import annotations
import queue
import socket
import threading
from xdevs.rt_sim.input_handler import InputHandler


class TCPServer:
    """
    TODO
    """
    def __init__(self, host, port, q):
        """
        TODO
        :param host:
        :param port:
        :param q:
        """
        self.host = host
        self.port = port

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients_connected: list[threading.Thread] = list()

        self.events_queue = q

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print('Server listening...')
        while True:
            client_socket, address = self.server_socket.accept()
            self.clients_connected.append(threading.Thread(target=client_handler, daemon=True,
                                                           args=(client_socket, address, self.events_queue)))
            self.clients_connected[len(self.clients_connected) - 1].start()

def client_handler(client_socket, addr, q):
    """Function to handle each client connection."""

    print(f'Connected to client {addr}')
    while True:
        data = client_socket.recv(1024)
        # No existe valor por defecto. Es obligatorio pasarle un valor.
        # 1024 por ser potencia de 2 y tener espacio de sobra.
        if not data:
            print(f'Connection with client {addr} closed')
            break
        q.put(data)


class TCPInputHandler(InputHandler):
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

        self.host: str = kwargs.get('host', 'LocalHost')

        self.port: int = kwargs.get('port')
        if self.port is None:
            raise ValueError('TCP port is mandatory')

        # A list to handle all the clients msgs
        self.event_queue = queue.SimpleQueue()

        # TCP server to handle the communications
        self.server = TCPServer(self.host, self.port, self.event_queue)
        self.server_thread: threading.Thread = threading.Thread(target=self.server.start, daemon=True)

    def initialize(self):
        self.server_thread.start()

    def run(self):
        while True:
            event = self.event_queue.get()
            self.push_event(event)


if __name__ == '__main__':
    input_queue = queue.SimpleQueue()

    TCP = TCPInputHandler(port=4321, queue=input_queue)
    TCP.initialize()
    TCP.run()
