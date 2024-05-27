from xdevs.models import Atomic, Port


class Generator(Atomic):
    def __init__(self, name: str, num_outputs: int = 1, period: float = float('inf'), num_ports: int = 1):
        super(Generator, self).__init__(name=name)
        if num_outputs < 1:
            raise ValueError('Number of outputs must greater than zero')
        if num_ports < 1:
            raise ValueError('Number of ports must be greater than zero')
        if period <= 0:
            raise ValueError('Period must be greater than zero')
        self.num_outputs: int = num_outputs
        self.period: float = period

        self.o_out: list[Port[int]] = [Port(int, f'o_out_{i}') for i in range(num_ports)]
        for port in self.o_out:
            self.add_out_port(port)

    def deltint(self):
        self.sigma = self.period

    def deltext(self, e: float):
        pass

    def lambdaf(self):
        for port in self.o_out:
            port.extend(range(self.num_outputs))

    def initialize(self):
        self.activate()

    def exit(self):
        pass
