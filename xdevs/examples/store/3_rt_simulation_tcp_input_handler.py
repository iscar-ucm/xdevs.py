import sys
import time
from xdevs.examples.store.models.msg import NewClient
from xdevs.rt import RealTimeCoordinator, RealTimeManager
from xdevs.examples.store.models.store import Store


def get_sec(time_str):
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)


def new_client_parser(msg: str):
    client_id, t_entered = msg.split('?')

    c = NewClient(client_id=client_id, t_entered=time.time())
    return c


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
        print("\t" "python3 " + sys.argv[0] +
              " <SIMULATION_TIME> <N_CASHIERS> <MEAN_TIME_TO_DISPATCH_CLIENT> <MEAN_TIME_BETWEEN_NEW_CLIENTS> "
              "<DISPATCHING_STDDEV> <NEW_CLIENTS_STDDEV> <FORCE_CHAIN>")
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
    print(f'\tSimulation time: {sim_time} seconds')
    print(f'\tNumber of Employees: {n_employees}')
    print(f'\tMean time required to dispatch clients: {mean_employees} seconds (stddev of {stddev_employees})')
    print(f'\tMean time between new clients: {mean_generator} seconds (standard deviation of {stddev_clients})')

    msg_parser = {
        'IP_NewClient': new_client_parser,
    }

    # Real Time simulation:
    start = time.time()
    store = Store(n_employees, mean_employees, mean_generator, stddev_employees, stddev_clients)
    middle = time.time()
    print(f'Model Created. Elapsed time: {middle - start} sec')
    rt_manager = RealTimeManager(max_jitter=0.2, event_window=3)
    rt_manager.add_input_handler('tcp', port=4321, max_clients=5, msg_parsers=msg_parser)

    c = RealTimeCoordinator(store, rt_manager)
    middle = time.time()
    print(f'Coordinator, Manager and Handlers Created. Elapsed time: {middle - start} sec')
    c.simulate_iters(time_interv=sim_time)
    end = time.time()
    print(f'Simulation time (s) = {sim_time}')
    print(f'Simulation took: {end - start} sec')
    print(f'Error (%) = {((time.time() - start - sim_time) / sim_time) * 100}')
