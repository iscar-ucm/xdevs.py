from __future__ import annotations
import queue
import socket
import threading
from typing import Any


def input_client_handler(client_socket: socket.socket, address: tuple[Any, ...],
                         input_queue: queue.SimpleQueue, max_size: int = 1024):
    """
    Function to handle a socket client that inputs external events to the simulation events.

    :param client_socket: socket assigned to the running client.
    :param address: socket address of the event source endpoint.
    :param input_queue: queue from the outside to the simulation. Messages are injected as raw byte arrays.
    :param max_size: maximum size of incoming messages (in bytes).
    """
    # TODO probablemente esto no tenga mucho sentido aquí y la lógica es mejor que la hagan los handlers
    print(f'socket input client connected to {address}')
    try:
        while True:
            data = client_socket.recv(max_size)
            if not data:  # connection closed
                break
            input_queue.put(data)
    finally:
        print(f'socket input client disconnected from {address}')
        client_socket.close()


def output_client_handler(client_socket: socket.socket, address: tuple[Any, ...], output_queue: queue.SimpleQueue):
    """
    Function to handle a TCP socket client that outputs simulation events to the outside.

    :param client_socket: socket assigned to the running client.
    :param address: socket address of the event destination endpoint.
    :param output_queue: queue from simulation to outside. Messages are already parsed as strings
    """
    # TODO Podemos tener sockets tanto servidor como clientes para inputs y outputs
    # TODO probablemente esto no tenga mucho sentido aquí y la lógica es mejor que la hagan los handlers
    print(f'socket output client connected to {address}')
    try:
        while True:
            event = output_queue.get()
            client_socket.sendall(event.encode())
    except OSError as e:
        # If a system error occurred when connecting, we assume that the server has been shut down.
        print(f'Error while connecting to server: {e}')
    finally:
        print(f'socket output client disconnected from {address}')
        client_socket.close()


class SocketServer:
    def __init__(self, server_address: tuple[Any, ...], server_socket: socket.socket = None, max_clients: int = None):
        """
        TCP server that manages the connectivity with TCP clients for inputting events.

        :param server_address: server address used when binding the server socket.
               Usually, it is a tuple (IP address, socket number). However, this depends on the socket type used.
        :param server_socket: server socket. By default, it uses the IPv4 family and socket stream type.
        :param max_clients: maximum number of clients allowed concurrently. By default, it is None (i.e., no limit).
        """
        # TODO idea loca: el servidor añade a una cola de clientes los nuevos clientes y se olvida.
        # TODO es la responsabilidad del handler de turno hacer lo que sea que tiene que hacer con los sockets
        self.server_address: tuple[Any, ...] = server_address
        if server_socket is None:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket: socket.socket = server_socket
        self.max_clients: int | None = max_clients
        self.clients: list[threading.Thread] = list()  # TODO yo creo que nos lo podemos ahorrar

        self.input_queue: queue.SimpleQueue = queue.SimpleQueue() # Para InputHandler
        self.output_queue: queue.SimpleQueue = queue.SimpleQueue() # Para OutputHandler

    def start_ih(self):
        self.server_socket.bind(self.server_address)
        self.server_socket.listen(self.max_clients)
        print(f'socket server with address {self.server_address} is listening...')
        while True:
            client_socket, address = self.server_socket.accept()
            # TODO en vez de esto, añadimos el resultado de eaccept a la cola
            # TODO la hebra etc. la abre el handler de turno
            self.clients.append(threading.Thread(target=input_client_handler, daemon=True,
                                                 args=(client_socket, address, self.input_queue)))
            #print('TCP MSG ARRIVED')
            self.clients[-1].start()

    def start_oh(self):
        self.server_socket.connect(self.server_address)
        print('Connected to server...')
        c_thread = threading.Thread(target=output_client_handler, daemon=True,
                                    args=(self.server_socket, self.server_address, self.output_queue))
        c_thread.start()


