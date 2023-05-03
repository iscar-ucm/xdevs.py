import socket
import time
import threading
from typing import Any, Callable

from xdevs.rt_sim.output_handler import OutputHandler


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

        self.host: str = kwargs.get('host', 'LocalHost')
        self.port: int = kwargs.get('port')
        if self.port is None:
            raise ValueError('TCP port is mandatory')
        self.t_wait: float = kwargs.get('t_wait', 10)

        self.event_parser: Callable[[str, Any], str] = kwargs.get('event_parser', lambda port, msg: f'{port},{msg}')

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.is_connected: bool = False

    def exit(self):
        print(f'Closing client to server {self.host} in port {self.port}...')
        self.client_socket.close()
        self.is_connected = False

    def run(self):
        timeout = 0
        while True:
            # Wait for an outgoing event
            event = self.pop_event()
            try:
                if self.is_connected:
                    if self.client_socket.fileno() > 0:  # TODO no podemos usar esto en lugar de self.is_connected?
                        # We can only send data if the client_socket is not close. Client_socket is closed when
                        # .fileno() return 0
                        self.client_socket.sendall(event.encode())
                elif time.time() > timeout:
                    try:

                        self.client_socket.connect((self.host, self.port))
                        print('Connected to server...')

                        self.is_connected = True
                        # TODO el mensaje habría que inyectarlo!!

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


if __name__ == '__main__':

    def inject_msg():
        print(f'Thread active')
        for i in range(20):
            TCP.queue.put(('Port', f' msg: {i} '))
            print(f'Msg in q and i = {i}')
            if i == 3:
                time.sleep(15)
            else:
                time.sleep(2.5)
        TCP.exit()
        print('Closing...')


    TCP = TCPOutputHandler(host='LocalHost', port=4321)
    t = threading.Thread(target=inject_msg, daemon=True)
    t.start()
    TCP.run()
