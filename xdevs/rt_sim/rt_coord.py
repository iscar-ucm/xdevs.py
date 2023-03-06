from xdevs.models import Coupled
from xdevs.rt_sim.rt_manager import RtManager
from xdevs.sim import Coordinator


class CoordinatorRt(Coordinator):

    def __init__(self, model: Coupled, manager: RtManager):
        super().__init__(model)

        self.manager = manager
        self.time_scale = manager.time_scale
        self.max_delay = manager.max_delay

    def initialize(self):
        super().initialize()
        self.manager.initialize(self.clock.time)

    def simulate(self, time_interv: float = 10000):
        self.clock.time = 0

        while self.clock.time < time_interv:
            if self.time_next == float("inf"):  # comprobacion del evento_handler
                print("infinity reached")
                break
            t_sleep = self.time_next - self.clock.time
            slept, msgs = self.manager.sleep(self.time_next)
            for m in msgs:
                port = self.model.get_in_port(m[0])
                if port is not None:
                    try:
                        port.add(m[1])
                    except TypeError as e:
                        print(f'{e}')
                else:
                    print(f'{m[0]} does not exit')
                slept = min(t_sleep, slept)

            # UPDATE SIMULATION CLOCK
            self.clock.time = slept
            # EXECUTE NEXT CYCLE
            if self.clock.time == self.time_next:  # now lambdas are optional
                self.lambdaf()
            self.deltfcn()
            self._execute_transducers()
            self.clear()

        self.manager.exit(self.clock.time)
