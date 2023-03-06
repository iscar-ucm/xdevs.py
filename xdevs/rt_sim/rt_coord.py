from xdevs.models import Coupled
from xdevs.rt_sim.rt_manager import RealTimeManager
from xdevs.sim import Coordinator


class RealTimeCoordinator(Coordinator):
    def __init__(self, model: Coupled, manager: RealTimeManager):
        super().__init__(model)
        self.manager: RealTimeManager = manager

    def initialize(self):
        super().initialize()
        self.manager.initialize(self.clock.time)

    def exit(self):
        self.manager.exit(self.clock.time)
        super().exit()

    def simulate(self, time_interv: float = 10000):
        self.initialize()
        while self.clock.time < time_interv:
            if self.time_next == float("inf") and not self.manager.event_handlers:  # solo paramos si no hay handlers!
                print('infinity reached')
                break
            t, msgs = self.manager.sleep(self.time_next)
            # INJECT EXTERNAL EVENTS
            for port_id, msg in msgs:
                port = self.model.get_in_port(port_id)
                if port is not None:
                    try:
                        port.add(msg)
                    except TypeError as e:
                        print(f'invalid message type: {e}')
                else:
                    print(f'input port {port_id} does not exit')
            # UPDATE SIMULATION CLOCK
            self.clock.time = t
            # EXECUTE NEXT CYCLE
            if self.clock.time == self.time_next:  # now lambdas are optional
                self.lambdaf()
            self.deltfcn()
            self._execute_transducers()
            self.clear()
        self.exit()
