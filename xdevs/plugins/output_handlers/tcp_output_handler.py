import socket
import time
import threading

from xdevs.rt_sim.output_handler import OutputHandler

# This will be a client that subscribe to a server to send the outgoing event of the system.

def clear_queue(q):
    """Function that removes all elements in a queue."""
    try:
        while not q.empty():
            q.get()
    except TypeError as e:
        print(f'Argument in clear_queue must be a queue type: {e}')

def tcp_default_format(port, msg):
    """Default format for outgoing events."""
    return f'{port},{msg}'


class TCPOutputHandler(OutputHandler):
    def __init__(self, **kwargs):
        """
        TCPOutHandler is a socket client that sends to a server (described as host, port) the outgoing events of the
        system. By default, the events are in the form: port, msg.

        TODO:  si el handler se ha conectado mas tarde al servidor enviara toda la cola de golpe.
                posibles soluciones:    1) poner una espera para que se envie uno por linea
                                        2) borrar toda la cola anterior. <- OFS apoya esta

        :param str host: is the IP of the device where the server is hosted. Default is 'LocalHost'.
        :param int port: is the port in which the host is listening.
        :param float t_wait: is the time (in s) for trying to reconnect to the server if a ConnectionRefusedError
            exception occurs. Default is 10 s.
        :param Callable[[Any, Any], str] event_parser: A function that determines the format of outgoing events. By
            default, the format is 'port,msg', where 'port' is the name of the port in which an event occurred, and
            'msg' is the message given by the port.

        """
        super().__init__()

        self.host = kwargs.get('host', 'LocalHost')

        self.port = kwargs.get('port')
        if self.port is None:
            raise ValueError('port is mandatory')

        self.t_wait = kwargs.get('t_wait', 10)

        self.event_parser = kwargs.get('event_parser', tcp_default_format)

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.lock = None

    def exit(self):
        print(f'CLosing client to server {self.host} in port {self.port}...')
        self.lock = False
        self.client_socket.close()

    def run(self):
        self.lock = True
        while True:
            # First we connect to the server.
            while self.lock:
                try:
                    self.client_socket.connect((self.host, self.port))
                    print('Connected to server...')
                    clear_queue(self.queue)     # TODO solucion 2
                    self.lock = False
                except ConnectionRefusedError:
                    # If the connection is refused, wait for a time t_wait and try again.
                    # This exception can be raised when: the port is blocked or closed by a firewall, host is not
                    # available or close, among others.
                    print(f'Connection refused, trying again in {self.t_wait} s. ')
                    time.sleep(self.t_wait)
                except OSError as e:
                    # If a system error occurred when connecting, we assume that the server has been shut down.
                    print(f'Error while connecting to server: {e}')
                    self.lock = False

            # If the connection was a success.


            # First we check for outgoing events
            port, msg = self.queue.get()

            # If an outgoing event occurs it is sent to the server ,but first it is formatted.

            data = self.event_parser(port, msg)

            if self.client_socket.fileno() > 0:
                # We can only send data if the client_socket is not close. Client_socket is closed when .fileno() return
                # 0
                self.client_socket.sendall(data.encode())
                # time.sleep(0.1) TODO solucion 1

            print(f'msg sent: {data}')


if __name__ == '__main__':

    def inject_msg():
        print(f'Thread active')
        for i in range(20):
            TCP.queue.put(('Port', f' msg: {i} '))
            print(f'Msg in q and i = {i}')
            time.sleep(2.5)
        TCP.exit()
        print('Closing...')


    TCP = TCPOutputHandler(host='LocalHost', port=4321)
    t = threading.Thread(target=inject_msg, daemon=True)
    t.start()
    TCP.run()
