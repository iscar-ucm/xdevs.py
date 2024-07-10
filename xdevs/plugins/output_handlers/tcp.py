from __future__ import annotations
import time
from typing import Any, Callable

from xdevs.plugins.util.socket_server import SocketServer
from xdevs.abc.handler import OutputHandler


class TCPOutputHandler(OutputHandler):  # TODO cambiar a SocketClientOutputHandler (más generico que TCP, abre la puerta a SocketServerOutputHandler)
    def __init__(self, **kwargs):
        """
        TCPOutHandler is a socket client that sends to a server (described as host, port) the outgoing events of the
        system. By default, the events are in the form: port, msg.

        :param str host: is the IP of the device where the server is hosted. Default is 'LocalHost'.
        :param int port: is the port in which the host is listening.
        :param float t_wait: is the time (in s) for trying to reconnect to the server if a ConnectionRefusedError
            exception occurs. Default is 10 s.
        :param Callable[[str, Any], str] event_parser: A function that determines the format of outgoing events. By
            default, the format is 'port,msg', where 'port' is the name of the port in which an event occurred, and
            'msg' is the message given by the port.

        """
        super().__init__(**kwargs)

        self.client_address: tuple[Any, ...] = kwargs.get('address')
        if self.client_address is None:
            host: str = kwargs.get('host', 'LocalHost')
            port: int = kwargs.get('port')
            if port is None:
                raise ValueError('TCP port is mandatory')
            self.client_address = (host, port)

        self.server_socket = kwargs.get('server_socket')

        self.client = SocketServer(server_address=self.client_address, server_socket=self.server_socket)

        self.t_wait: float = kwargs.get('t_wait', 10)

        self.event_parser: Callable[[str, Any], str] = kwargs.get('event_parser', lambda port, msg: f'{port},{msg}')

        # self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.is_connected: bool = False

#    def exit(self):
#        print(f'Closing client to server {host} in port {self.port}...')
#        self.client_socket.close()
#        self.is_connected = False

    def run(self):
        timeout = 0     # Probar a poner aqui time.time() y ver que pasa
        while True:
            # Wait for an outgoing event
            event = self.pop_event()
            try:
                if self.is_connected:
                    # self.client_socket.sendall(event.encode())
                    self.client.output_queue.put(event)
                elif time.time() > timeout:
                    try:

                        # self.client_socket.connect((self.host, self.port))
                        # print('Connected to server...')

                        self.client.start_oh()

                        self.is_connected = True
                        # self.client_socket.sendall(event.encode())

                        self.client.output_queue.put(event)

                    except ConnectionRefusedError:
                        # If the connection is refused, wait for a time t_wait and try again.
                        # This exception can be raised when: the port is blocked or closed by a firewall, host is not
                        # available or close, among others.
                        print(f'Connection refused, trying again in {self.t_wait} s.')
                        # Si un outgoing event tardase mas de self.t_wait, se conectaría cuando llegase dicho event.
                        timeout = time.time() + self.t_wait

            except OSError as e:
                # If a system error occurred when connecting, we assume that the server has been shut down.
                print(f'Error while connecting to server: {e}')
                break
