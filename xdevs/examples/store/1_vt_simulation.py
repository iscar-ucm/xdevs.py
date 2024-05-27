import sys
import time
from xdevs.sim import Coordinator
from xdevs.examples.store.models.store import Store


def get_sec(time_str):
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)


if __name__ == '__main__':
    sim_time: float = 13
    n_employees = 3
    mean_employees = 5
    mean_generator = 3
    stddev_employees = 0
    stddev_clients = 0

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

    # PURE SIMULATION
    start = time.time()
    store = Store(n_employees, mean_employees, mean_generator, stddev_employees, stddev_clients)
    middle = time.time()
    print("Model Created. Elapsed time: {} sec".format(middle - start))
    coord = Coordinator(store)
    coord.initialize()
    middle = time.time()
    print("Coordinator Created. Elapsed time: {} sec".format(middle - start))
    coord.simulate(sim_time)
    end = time.time()
    print("Simulation took: {} sec".format(end - start))
