import sys

from xdevs.examples.store.models.msg import NewClient
from xdevs.models import Coupled, Port
from xdevs.rt import RealTimeCoordinator, RealTimeManager
import time

from xdevs.examples.store.models.clients import ClientGenerator


class GenSys(Coupled):
    def __init__(self, mean_clients: float = 1, stddev_clients: float = 0, name=None):
        super().__init__(name)
        generator = ClientGenerator(mean_clients, stddev_clients)

        self.out_gen_port = Port(NewClient, 'Gen_ClientOut')
        self.add_out_port(self.out_gen_port)

        self.add_component(generator)

        self.add_coupling(generator.output_new_client, self.out_gen_port)


def get_sec(time_str):
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)


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
                                                                                          stddev_employees))

    start = time.time()
    gensys = GenSys(mean_generator, stddev_clients)
    middle = time.time()
    print("Model Created. Elapsed time: {} sec".format(middle - start))
    rt_manager = RealTimeManager(max_jitter=0.2, event_window=0.5)
    rt_manager.add_output_handler('mqtt_handler')
    c = RealTimeCoordinator(gensys, rt_manager)
    middle = time.time()
    print("Coordinator and Manager Created. Elapsed time: {} sec".format(middle - start))
    c.simulate_rt(time_interv=sim_time)
    end = time.time()
    print(f' Simulation time (s) = {sim_time}')
    print("Simulation took: {} sec".format(end - start))
    print(f' Error (%) = {((time.time() - start - sim_time) / sim_time) * 100}')
