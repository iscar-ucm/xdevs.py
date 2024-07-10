from random import gauss
from xdevs.models import Atomic, Port
import time
from .msg import NewClient


class ClientGeneratorStatus:
    def __init__(self):
        self.next_client_id: int = 0
        self.time_to_next: float = 0

    def __str__(self):
        return f'<next: {self.next_client_id}: in: {self.time_to_next}>'


class ClientGenerator(Atomic):
    def __init__(self, mean: float = 10, stddev: float = 0, name: str = None):
        super().__init__(name)
        self.mean: float = mean
        self.stddev: float = stddev
        self.clock: float = 0
        self.state: ClientGeneratorStatus = ClientGeneratorStatus()

        self.output_new_client: Port[NewClient] = Port(NewClient)
        self.add_out_port(self.output_new_client)

        self.time_started: float = time.time()

    def deltint(self):
        self.clock += self.sigma
        self.state.next_client_id += 1
        self.state.time_to_next = max(gauss(self.mean, self.stddev), 0)
        # Para simulacion
        # print('({}) [{}]-> {}'.format(self.clock, self.name, str(self.state)))
        # Para RT
        print('({:.4f}) [{}]-> {}'.format(time.time()-self.time_started, self.name, str(self.state)))
        self.hold_in(self.phase, self.state.time_to_next)

    def deltext(self, e):
        pass

    def lambdaf(self):
        self.output_new_client.add(NewClient(self.state, self.clock + self.sigma))

    def initialize(self):
        self.activate()

    def exit(self):
        pass
