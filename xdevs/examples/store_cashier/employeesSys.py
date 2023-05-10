import time

from xdevs.examples.store_cashier.employee import Employee
from xdevs.examples.store_cashier.msg import LeavingClient, ClientToEmployee, NewClient
from xdevs.models import Coupled, Port
from xdevs.rt_sim import RealTimeManager, RealTimeCoordinator


class EmployeesSys(Coupled):
    def __init__(self, n_employees: int = 100, mean_employees: float = 5,
                 stddev_employees: float = 0, name=None):
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

    # class ClientToEmployee:
    #     def __init__(self, new_client, employee_id):
    #         self.client = new_client
    #         self.employee_id = employee_id

    # Estoy pasando : MqttClient?i?t

def input_client_parser(msg: str):
    client, e_id = msg.split('?')
    c = ClientToEmployee(NewClient(client, time.time()-t_ini), int(e_id))
    return c


if __name__ == '__main__':
    sim_time = 50

    E = EmployeesSys()

    e_manager = RealTimeManager(max_jitter=0.2, event_window=0.5)

    msg_parser = {
        'InputClient': input_client_parser,
    }

    sub = {
        'RTsys/InputClient': 0,
        'RTsys/AvailableEmployee': 0
    }

    e_manager.add_input_handler('mqtt_handler', subscriptions=sub, msg_parsers=msg_parser)

    e_manager.add_output_handler('csv_out_handler')

    e_coord = RealTimeCoordinator(E, e_manager)

    t_ini = time.time()
    print(f' >>> COMENZAMOS : {t_ini}')
    e_coord.simulate(time_interv=sim_time)
    print(f' >>> FIN : {time.time()}')
    print(f' Tiempo a ejecutar (s) = {sim_time}')
    print(f' Tiempo ejecutado (s) = {(time.time() - t_ini)}')
    print(f' Error (%) = '
          f'{((time.time() - t_ini - sim_time) / sim_time) * 100}')
