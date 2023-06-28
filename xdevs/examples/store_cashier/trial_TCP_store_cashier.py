import sys
import threading

from xdevs.examples.store_cashier.msg import NewClient, ClientToEmployee, LeavingClient
from xdevs.models import Coupled, Port
from xdevs.sim import Coordinator
from xdevs.rt_sim.rt_coord import RealTimeCoordinator
from xdevs.rt_sim.rt_manager import RealTimeManager
import time

from client_generator import ClientGenerator
from store_queue import StoreQueue
from employee import Employee


class StoreCashier(Coupled):
    def __init__(self, n_employees: int = 10000, mean_employees: float = 30, mean_clients: float = 1,
                 stddev_employees: float = 0, stddev_clients: float = 0,
                 name=None):
        super().__init__(name)

        generator = ClientGenerator(mean_clients, stddev_clients)
        queue = StoreQueue()

        self.add_component(generator)
        self.add_component(queue)
        self.add_coupling(generator.output_new_client, queue.input_new_client)

        self.new_client = Port(NewClient, 'NewClient')
        self.add_in_port(self.new_client)
        self.add_coupling(self.new_client, queue.input_new_client)

        for i in range(n_employees):
            employee = Employee(i, mean_employees, stddev_employees)
            self.add_component(employee)
            self.add_coupling(queue.output_client_to_employee, employee.input_client)
            self.add_coupling(employee.output_ready, queue.input_available_employee)



def get_sec(time_str):
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)

def new_client_parser(msg: str):
    #print('¿?¿?¿?¿?¿?')
    client_id, t_entered = msg.split('?')

    c = NewClient(client_id=client_id,t_entered=time.time())
    #print(f'DEVUELVO:{c}, c_id = {client_id}, t = {t_entered} ahora {time.time()}')
    return c

def tcp_parser(event):
    pass



if __name__ == '__main__':
    sim_time: float = 52
    n_employees = 3
    mean_employees = 5
    mean_generator = 3
    stddev_employees = 0.8
    stddev_clients = 0.5

    if len(sys.argv) > 8:
        print("Program used with more arguments than accepted. Last arguments will be ignored.")
    elif len(sys.argv) < 8:
        print("Program used with less arguments than accepted. Missing parameters will be set to their default value.")
    if len(sys.argv) != 8:
        print("Correct usage:")
        print("\t" "python3 " + sys.argv[
            0] + " <SIMULATION_TIME> <N_CASHIERS> <MEAN_TIME_TO_DISPATCH_CLIENT> <MEAN_TIME_BETWEEN_NEW_CLIENTS> <DISPATCHING_STDDEV> <NEW_CLIENTS_STDDEV> <FORCE_CHAIN>")
    try:
        sim_time = get_sec(sys.argv[1])
        n_employees = int(sys.argv[2])
        mean_employees = float(sys.argv[3])
        mean_generator = float(sys.argv[4])
        stddev_employees = float(sys.argv[5])
        stddev_clients = float(sys.argv[6])
        force_chain = bool(int(sys.argv[7]))
    except IndexError:
        pass

    print("CONFIGURATION OF THE SCENARIO:")
    print("\tSimulation time: {} seconds".format(sim_time))
    print("\tNumber of Employees: {}".format(n_employees))
    print("\tMean time required by employee to dispatch clients: {} seconds (standard deviation of {})".format(
        mean_employees, stddev_employees))
    print("\tMean time between new clients: {} seconds (standard deviation of {})".format(mean_generator,
                                                                                          stddev_clients))

#####


msg_parser = {
    'NewClient': new_client_parser,
}


# Real Time simulation:



start = time.time()
store = StoreCashier(n_employees, mean_employees, mean_generator, stddev_employees, stddev_clients)
middle = time.time()
print("Model Created. Elapsed time: {} sec".format(middle - start))
rt_manager = RealTimeManager(max_jitter=0.2, event_window=3)
rt_manager.add_input_handler('tcp_handler', port=4321, max_clients=5, msg_parsers=msg_parser)

c = RealTimeCoordinator(store, rt_manager)
middle = time.time()
print("Coordinator, Manager and Handlers Created. Elapsed time: {} sec".format(middle - start))
c.simulate(time_interv=sim_time)
end = time.time()
print(f' Simulation time (s) = {sim_time}')
print("Simulation took: {} sec".format(end - start))
print(f' Error (%) = '
      f'{((time.time() - start - sim_time) / sim_time) * 100}')
