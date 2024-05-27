import sys
import time
from xdevs.examples.store.models.msg import NewClient
from xdevs.rt import RealTimeCoordinator, RealTimeManager
from xdevs.examples.store.models.store import StoreWithoutGen


def get_sec(time_str):
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)


def mqtt_parser(msg: str):
    c_id, t = msg.split(';')
    return NewClient(c_id, t)


if __name__ == '__main__':
    sim_time: float = 52
    n_employees = 3
    mean_employees = 5
    stddev_employees = 0.8

    if len(sys.argv) > 8:
        print("Program used with more arguments than accepted. Last arguments will be ignored.")
    elif len(sys.argv) < 8:
        print(
            "Program used with less arguments than accepted. Missing parameters will be set to their default value.")
    if len(sys.argv) != 8:
        print("Correct usage:")
        print("\tpython3 " + sys.argv[0] + " <SIM_TIME> <N_CASHIERS> <MEAN_DISPATCH_TIME> <STDDEV_DISPATCH>")
    try:
        sim_time = get_sec(sys.argv[1])
        n_employees = int(sys.argv[2])
        mean_employees = float(sys.argv[3])
        stddev_employees = float(sys.argv[4])
    except IndexError:
        pass

    print("CONFIGURATION OF THE SCENARIO:")
    print(f"\tSimulation time: {sim_time} seconds")
    print(f"\tNumber of Employees: {n_employees}")
    print(f"\tMean time required to dispatch clients: {mean_employees} seconds (stddev of {stddev_employees})")

    conexiones = {
        'Gen_ClientOut': 'Queue_ClientGen'
    }
    topics = {'RTsys/Output/Gen_ClientOut': 0}

    msg_parser = {
        'Queue_ClientGen': mqtt_parser,
    }

    start = time.time()
    storeNOGEN = StoreWithoutGen(n_employees, mean_employees, stddev_employees)
    middle = time.time()
    print(f"Model Created. Elapsed time: {middle - start} sec")
    rt_manager = RealTimeManager(max_jitter=0.2, event_window=0.5)
    rt_manager.add_input_handler('mqtt', subscriptions=topics, connections=conexiones, msg_parsers=msg_parser)
    c = RealTimeCoordinator(storeNOGEN, rt_manager)
    middle = time.time()
    print(f"Coordinator and Manager Created. Elapsed time: {middle - start} sec")
    t_ini = time.time()
    c.simulate_iters(time_interv=sim_time)
    end = time.time()
    print(f' Simulation time (s) = {sim_time}')
    print(f"Simulation took: {end - start} sec")
    print(f' Error (%) = {((time.time() - start - sim_time) / sim_time) * 100}')
