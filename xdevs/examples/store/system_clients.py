from xdevs.examples.store.models.msg import NewClient
from xdevs.models import Coupled, Port
from xdevs.rt import RealTimeManager, RealTimeCoordinator
import time

from xdevs.examples.store.models.clients import ClientGenerator


class GenSys(Coupled):
    def __init__(self,  mean_clients: float = 1, stddev_clients: float =0, name=None):
        super().__init__(name)
        generator = ClientGenerator(mean_clients, stddev_clients)

        self.out_gen_port = Port(NewClient)
        self.add_out_port(self.out_gen_port)

        self.add_component(generator)

        self.add_coupling(generator.output_new_client, self.out_gen_port)


if __name__ == '__main__':
    sim_time = 30
    mean_clients = 3
    stddev_clients = 0

    gen = GenSys(mean_clients=mean_clients, stddev_clients=stddev_clients)

    gen_manager = RealTimeManager(max_jitter=0.2, event_window=0.5)
    gen_manager.add_output_handler('tcp', PORT=5055)

    gen_coord = RealTimeCoordinator(gen, gen_manager)

    t_ini = time.time()
    print(f' >>> COMENZAMOS : {t_ini}')
    gen_coord.simulate_iters(time_interv=sim_time)
    print(f' >>> FIN : {time.time()}')
    print(f' Tiempo a ejecutar (s) = {sim_time }')
    print(f' Tiempo ejecutado (s) = {(time.time() - t_ini)}')
    print(f' Error (%) = {((time.time() - t_ini - sim_time) / sim_time) * 100}')
