import queue
import socket
import threading

from xdevs.rt_sim.input_handler import InputHandler

# Server in which the ingoing event will be joining the system

def tcp_format(msg):
    """Default function for converting incoming msg to events. Incoming msg must be Port,msg."""
    return msg.decode().split(',')


def client_handler(client_socket, addr, parser_f, q):
    """Function to handle each client connection."""

    print(f'Connected to: {addr}')
    while True:
        data = client_socket.recv(1024)
        # No existe valor por defecto. Es obligatorio pasarle un valor.
        # 1024 por ser potencia de 2 y tener espacio de sobra.
        if not data:
            print(f'Connection closed with {addr}')
            break
        data = parser_f(data)
        # print(f'data to inyect in q is : {data}')
        q.put(data)
        # q.put((parser_f(data)))

class TCPInputHandler(InputHandler):
    def __init__(self, **kwargs):
        """
        TCPInputHandler is a socket server. The server receives the clients messages and inject them to the system as
        ingoing events.

        Default format for client messages must be: Port,msg. Be aware that all the clients must use the same format. If
        a different format is chosen a new function to parser them must be given (event_parser).

        It is recommended that to implement multiple clients with different message formats, create as many
        TCPInputHandlers as formats.

        :param str host: is the IP of the network interface on which  the server is listening for incoming connections.
            Interesting values are '127.0.0.1' for the loopback interface (LocalHost) or '0.0.0.0' for listening to all
            interfaces. Default is '0.0.0.0'
        :param int port: is the port in which the server is listening
        :param Callable[any, [str,str]] event_parser: A function that converts the messages of each client (any) to the
            correct ingoing event format required by the system (str, str). First str must be the port name for the
            ingoing event and the second one what is going to be injected in that port.
        """
        super().__init__(**kwargs)

        self.host = kwargs.get('host', '0.0.0.0')  # 0.0.0.0  -> listening to all interfaces. If the server is in the
        # same device use LocalHost

        self.port = kwargs.get('port')
        if self.port is None:
            raise ValueError('PORT is mandatory')

        if self.event_parser is None:
            self.event_parser = tcp_format


        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients_connected = list()


        # A list to handle all the clients msgs
        self.msg_q = queue.SimpleQueue()

    def initialize(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print('Server listening...')
        t = threading.Thread(target=self.queue_handler, daemon=True)
        t.start()

    def run(self):
        while True:
            client_socket, address = self.server_socket.accept()
            self.clients_connected.append(threading.Thread(target=client_handler, daemon=True,
                                                   args=(client_socket, address, self.event_parser, self.msg_q)))
            self.clients_connected[len(self.clients_connected)-1].start()

    def queue_handler(self):
        """Messages from each client are pushed to the queue."""
        while True:
            port, msg = self.msg_q.get()
            # msg is parser into the port type.
            msg = self.msg_parsers.get(port, lambda x: x)(msg)
            # print(f'MENSAJE RECIBIDO E INYECTADO: {port, msg}')
            self.push_to_queue(port, msg)


if __name__ == '__main__':

    input_queue = queue.SimpleQueue()

    TCP = TCPInputHandler(port=4321, queue=input_queue)
    TCP.initialize()
    TCP.run()
