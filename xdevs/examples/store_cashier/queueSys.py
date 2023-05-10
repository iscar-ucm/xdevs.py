import time

from xdevs.examples.store_cashier.msg import ClientToEmployee, NewClient
from xdevs.examples.store_cashier.store_queue import StoreQueue
from xdevs.models import Coupled, Port
from xdevs.rt_sim import RealTimeManager, RealTimeCoordinator


class QueueSys(Coupled):
    def __init__(self, name=None):
        super().__init__(name)

        q_atomic = StoreQueue()
        self.add_component(q_atomic)
        # Available ports of queue component:
        # self.input_new_client = port(newclient)
        # self.input_available_employee = port(int)
        # self.output_client_to_employee = port(clienttoemployee)

        self.input_new_client = Port(NewClient, 'NewClient')
        self.input_available_employee = Port(int, 'AvailableEmployee')
        self.output_client_to_employee = Port(ClientToEmployee, 'Client2Employee')

        self.add_in_port(self.input_available_employee)
        self.add_in_port(self.input_new_client)
        self.add_out_port(self.output_client_to_employee)

        self.add_coupling(self.input_new_client, q_atomic.input_new_client)
        self.add_coupling(self.input_available_employee, q_atomic.input_available_employee)
        self.add_coupling(q_atomic.output_client_to_employee, self.output_client_to_employee)


def parser_new_client(msg: str):
    client_id, t_entered = msg.split('?')
    return NewClient(client_id, t_entered)


if __name__ == '__main__':
    sim_time = 60
    q = QueueSys()

    q_manager = RealTimeManager(max_jitter=0.2, event_window=0.5)

    msg_parser = {
        'NewClient': parser_new_client,
        'AvailableEmployee': lambda x: int(x)
    }

    q_manager.add_input_handler('tcp_handler', port=5055, max_clients=5, msg_parsers=msg_parser)

    subs = {
        'AvailableEmployee': 0,
    }

    q_manager.add_output_handler('mqtt_handler', )

    q_manager.add_output_handler('mqtt_handler')

    q_coord = RealTimeCoordinator(q, q_manager)

    t_ini = time.time()
    print(f' >>> COMENZAMOS : {t_ini}')
    q_coord.simulate(time_interv=sim_time)
    print(f' >>> FIN : {time.time()}')
    print(f' Tiempo a ejecutar (s) = {sim_time}')
    print(f' Tiempo ejecutado (s) = {(time.time() - t_ini)}')
    print(f' Error (%) = '
          f'{((time.time() - t_ini - sim_time) / sim_time) * 100}')
