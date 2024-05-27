from _collections import deque
from xdevs.models import Atomic, Port, INFINITY
import time
from .msg import NewClient, ClientToEmployee


class QueueStatus:
    def __init__(self):
        self.clients = deque()
        self.employees = deque()
        self.pairings = deque()

    def __str__(self):
        return f'<clients: {len(self.clients)}; employees: {len(self.employees)}; pairings: {len(self.pairings)}>'


class StoreQueue(Atomic):
    def __init__(self, name: str = None):
        super().__init__(name)
        self.clock = 0
        self.state = QueueStatus()

        self.input_new_client = Port(NewClient, 'in_new_client')
        self.input_available_employee = Port(int, 'in_available_employee')
        self.add_in_port(self.input_new_client)
        self.add_in_port(self.input_available_employee)

        self.output_client_to_employee = Port(ClientToEmployee, 'OUTqueue')
        self.add_out_port(self.output_client_to_employee)

        self.time_started = time.time()

    def deltint(self):
        self.clock += self.ta()
        self.state.pairings.clear()
        self.passivate()

    def deltext(self, e):
        self.clock += e
        for employee_id in self.input_available_employee.values:
            try:
                self.state.pairings.appendleft(ClientToEmployee(self.state.clients.pop(), employee_id))
            except IndexError:
                self.state.employees.appendleft(employee_id)
        for new_client in self.input_new_client.values:
            try:
                self.state.pairings.appendleft(ClientToEmployee(new_client, self.state.employees.pop()))
            except IndexError:
                self.state.clients.appendleft(new_client)
        # Para simulacion normal
        # print('({}) [{}]-> {}'.format(self.clock, self.name, str(self.state)))
        # Para RT
        print('({:.4f}) [{}]-> {}'.format(time.time()-self.time_started, self.name, str(self.state)))
        timeout = 0 if self.state.pairings else INFINITY
        self.hold_in(self.phase, timeout)

    def lambdaf(self):
        for pairing in self.state.pairings:
            self.output_client_to_employee.add(pairing)

    def initialize(self):
        self.passivate()

    def exit(self):
        pass
