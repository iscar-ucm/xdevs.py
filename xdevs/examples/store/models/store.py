from xdevs.models import Coupled, Port
from xdevs.examples.store.models.msg import NewClient, ClientToEmployee, LeavingClient
from xdevs.examples.store.models.clients import ClientGenerator
from xdevs.examples.store.models.queue import StoreQueue
from xdevs.examples.store.models.employee import Employee


class Store(Coupled):
    def __init__(self, n_employees: int = 10000, mean_employees: float = 30, mean_clients: float = 1,
                 stddev_employees: float = 0, stddev_clients: float = 0, name=None):
        super().__init__(name)

        generator = ClientGenerator(mean_clients, stddev_clients)
        queue = StoreQueue()

        self.input_new_client = Port(NewClient, 'IP_NewClient')
        self.add_in_port(self.input_new_client)

        self.output_port_queue = Port(ClientToEmployee, 'OP_LeavingQueue')
        self.output_port_gen = Port(NewClient, 'OP_LeavingGenerator')
        self.output_port_employee = Port(LeavingClient, 'OP_LeavingEmployee')

        self.add_out_port(self.output_port_queue)
        self.add_out_port(self.output_port_gen)
        self.add_out_port(self.output_port_employee)

        self.add_component(generator)
        self.add_component(queue)

        self.add_coupling(self.input_new_client, queue.input_new_client)
        self.add_coupling(generator.output_new_client, queue.input_new_client)
        self.add_coupling(queue.output_client_to_employee, self.output_port_queue)
        self.add_coupling(generator.output_new_client, self.output_port_gen)

        for i in range(n_employees):
            employee = Employee(i, mean_employees, stddev_employees)
            self.add_component(employee)
            self.add_coupling(queue.output_client_to_employee, employee.input_client)
            self.add_coupling(employee.output_ready, queue.input_available_employee)
            self.add_coupling(employee.output_client, self.output_port_employee)


class GenSys(Coupled):
    def __init__(self, mean_clients: float = 1, stddev_clients: float = 0, name=None):
        super().__init__(name)
        generator = ClientGenerator(mean_clients, stddev_clients)

        self.out_gen_port = Port(NewClient)
        self.add_out_port(self.out_gen_port)

        self.add_component(generator)

        self.add_coupling(generator.output_new_client, self.out_gen_port)


class StoreWithoutGen(Coupled):
    def __init__(self, n_employees: int = 10000, mean_employees: float = 30, stddev_employees: float = 0,
                 name=None):
        super().__init__(name)

        queue = StoreQueue()

        self.o_p_queue = Port(ClientToEmployee)
        self.add_out_port(self.o_p_queue)

        self.i_port_gen = Port(NewClient)
        self.add_in_port(self.i_port_gen)

        self.add_component(queue)

        self.add_coupling(self.i_port_gen, queue.input_new_client)

        self.add_coupling(queue.output_client_to_employee, self.o_p_queue)

        for i in range(n_employees):
            employee = Employee(i, mean_employees, stddev_employees)
            self.add_component(employee)
            self.add_coupling(queue.output_client_to_employee, employee.input_client)
            self.add_coupling(employee.output_ready, queue.input_available_employee)
