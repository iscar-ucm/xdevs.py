import datetime
import time

from xdevs.examples.store.models.employee import Employee
from xdevs.examples.store.models.msg import LeavingClient, ClientToEmployee, NewClient
from xdevs.models import Coupled, Port
from xdevs.rt import RealTimeManager, RealTimeCoordinator


class EmployeesSys(Coupled):
    def __init__(self, n_employees: int = 3, mean_employees: float = 10,
                 stddev_employees: float = 0.8, name=None):
        super().__init__(name)

        # A single Employee has:
        #        self.input_client = Port(ClientToEmployee)
        #        self.output_ready = Port(int)
        #        self.output_client = Port(LeavingClient)

        self.input_client = Port(ClientToEmployee, 'InputClient')
        self.output_ready = Port(int, 'OutputReady')
        self.output_client = Port(LeavingClient, 'LeavingClient')

        self.add_in_port(self.input_client)
        self.add_out_port(self.output_client)
        self.add_out_port(self.output_ready)

        for i in range(n_employees):
            employee = Employee(i, mean_employees, stddev_employees)
            self.add_component(employee)
            self.add_coupling(self.input_client, employee.input_client)
            self.add_coupling(employee.output_ready, self.output_ready)
            self.add_coupling(employee.output_client, self.output_client)


def input_client_parser(msg: str):
    # ("Client::id::3; t_entered::time.time to Employee::3") Formato de entrada
    client = msg.split("::id::")[1].split(";")[0]
    # t = time.time() - float(msg.split("t_entered::")[1].split(" t")[0])
    t = time.time() - t_ini
    e_id = msg.split("Employee::")[1]
    return ClientToEmployee(NewClient(client, t), int(e_id))


if __name__ == '__main__':
    sim_time = 50

    E = EmployeesSys()


    msg_parser = {
        'InputClient': input_client_parser,
    }

    sub_input = {
        'RTsys/Output/Client2Employee': 0,
    }

    sub_output = { # QUITAR
        'RTsys/AvailableEmployee': 0
    }

    connections = {
        'Client2Employee': 'InputClient'
    }

    e_manager = RealTimeManager(max_jitter=0.2, event_window=0.5)
    e_manager.add_input_handler('mqtt', subscriptions=sub_input, msg_parsers=msg_parser, connections=connections)
    e_manager.add_output_handler('mqtt', subscriptions=sub_output)
    e_manager.add_output_handler('csv', file='employees.csv')

    e_coord = RealTimeCoordinator(E, e_manager)

    t_ini = time.time()
    print(f' >>> COMENZAMOS : {t_ini} : {datetime.datetime.now()}')
    e_coord.simulate_iters(time_interv=sim_time)
    print(f' >>> FIN : {time.time()}')
    print(f' Tiempo a ejecutar (s) = {sim_time}')
    print(f' Tiempo ejecutado (s) = {(time.time() - t_ini)}')
    print(f' Error (%) = {((time.time() - t_ini - sim_time) / sim_time) * 100}')
