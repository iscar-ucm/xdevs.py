import time
from random import gauss
from xdevs.models import Atomic, Port, INFINITY

from .msg import ClientToEmployee, LeavingClient


class EmployeeState:
    def __init__(self):
        self.clients_so_far = 0
        self.client = None
        self.time_remaining = 0

    def __str__(self):
        return f'<so far: {self.clients_so_far}; busy: {bool(self.client)}; for: {self.time_remaining}>'


class Employee(Atomic):
    def __init__(self, employee_id: int, mean: float = 30, stddev: float = 0, name: str = None):
        super().__init__(name)
        self.name += str(employee_id)
        self.employee_id = employee_id
        self.mean = mean
        self.stddev = stddev
        self.clock = 0
        self.state = EmployeeState()

        self.input_client = Port(ClientToEmployee, 'in_client')
        self.add_in_port(self.input_client)

        self.output_ready = Port(int, 'out_ready')
        self.output_client = Port(LeavingClient, 'out_client')
        self.add_out_port(self.output_ready)
        self.add_out_port(self.output_client)

        self.time_started = time.time()

    def deltint(self):
        self.clock += self.sigma
        self.state.client = None
        self.state.time_remaining = INFINITY
        self.hold_in(self.phase, self.state.time_remaining)

    def deltext(self, e):
        self.clock += e
        if self.state.client is not None:
            self.state.time_remaining -= e
        else:
            for pairing in self.input_client.values:
                if pairing.employee_id == self.employee_id:
                    self.state.clients_so_far += 1
                    self.state.client = pairing.client
                    self.state.time_remaining = max(gauss(self.mean, self.stddev), 0)
                    # Para simulacion
                    # print('({}) [{}]-> {}'.format(self.clock, self.name, str(self.state)))
                    # Para RT
                    print('({:.4f}) [{}]-> {}'.format(time.time() - self.time_started, self.name, str(self.state)))
                    #print(f'EMPAREJADO C-E EN:{datetime.datetime.now()}')
        self.hold_in(self.phase, self.state.time_remaining)

    def lambdaf(self):
        clock = self.clock + self.state.time_remaining
        if self.state.client is not None:
            self.output_client.add(LeavingClient(self.state.client.client_id, self.state.client.t_entered, clock))
        self.output_ready.add(self.employee_id)

    def initialize(self):
        self.activate()

    def exit(self):
        pass
