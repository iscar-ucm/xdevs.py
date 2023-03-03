import queue
import time as rt_time
from xdevs.models import Coupled
from xdevs.sim import Coordinator
from xdevs.simRt.ManagerRt import ManagerRt


class CoordinatorRt(Coordinator):

    def __init__(self, model: Coupled, manager: ManagerRt):
        super().__init__(model)

        self.manager = manager
        self.time_scale = manager.time_scale
        self.max_delay = manager.max_delay

    def initialize(self):
        super().initialize()
        self.manager.initialize()

    def simulate(self, time_interv: float = 10000):
        """
        Simulates the behavior of a DEVS model in real time over a specified time interval.

        :param time_interv: The time interval to simulate, in seconds. Default is 10000.
        """
        self.clock.time = 0
        tf = self.clock.time + time_interv

        t_before = rt_time.time()  # real time before executing lambdas and deltas
        t_after = t_before  # real time after executing lambdas and deltas
        total_delayed_t = 0.0  # delay compensation buffer

        while self.clock.time < tf:
            if self.time_next == float("inf"):
                print("infinity reached and no event handler configured")
                break
            # FIRST WE COMPUTE SLEEP TIME
            v_sleep = (self.time_next - self.clock.time)  # virtual sleep time
            r_sleep = v_sleep * self.time_scale - (t_after - t_before) - total_delayed_t  # real sleep time
            # THEN WE CHECK THAT DELAY IS NOT TOO BAD
            if r_sleep < 0:
                total_delayed_t = -r_sleep
                if total_delayed_t > self.max_delay:  # too much delay -> stop execution
                    raise RuntimeError('ERROR: to much delayed time ')
            else:  # Sleep is positive. time elapsed and delayed_time are small. Everything went well
                total_delayed_t = 0
                rt_time.sleep(r_sleep)
                t_before = rt_time.time()
                v_sleep = min(v_sleep, (t_before - t_after) / self.time_scale)
            # TIME TO SLEEP
            # UPDATE SIMULATION CLOCK AND STORE TIME BEFORE NEXT CYCLE
            self.clock.time += v_sleep
            # EXECUTE NEXT CYCLE
            if self.clock.time == self.time_next:  # now lambdas are optional
                self.lambdaf()
            self.deltfcn()
            self._execute_transducers()
            self.clear()
            # STORE TIME AFTER THE CYCLE
            t_after = rt_time.time()  # time after executing lambdas and deltas
        print("done")

    def executeTEMP(self, time_interv: float = 10000):
        t_a_sleep = 0
        self.clock.time = 0

        while self.clock.time < time_interv:
            if self.time_next == float("inf"):  # comprobacion del evento_handler
                print("infinity reached and no event handler configured")
                break

            t_sleep = self.time_next - self.clock.time
            #print(f' <<< t_sleep = {t_sleep}')
            slept, msgs = self.manager.sleep(t_sleep)
            t_b_sleep = rt_time.time()
            #print(f' <->-<-> Tiempo b m & deltas = {t_b_sleep}')
            for m in msgs:
                port = self.model.get_in_port(m[0])
                if port is not None:
                    try:
                        port.add(m[1])
                    except TypeError as e:
                        print(f'{e}')
                else:
                    print(f'{m[0]} does not exit')
                #print('## ACTUALIZAR V_TIME msgs ##')
                #print(f't_sleep = {t_sleep} , slept/t_scale = {slept / self.time_scale}')
                t_sleep = min(t_sleep, slept / self.time_scale)



                # Actualizar tiempo

            #print('## ACTUALIZAR V_TIME ##')
            #print(f't_sleep = {t_sleep} , slept/t_scale = {slept/self.time_scale}')
            #print(f' <<< t_sleep actualizado? = {t_sleep}')
            # UPDATE SIMULATION CLOCK
            #print(f' <<< clock.time = {self.clock.time}')
            self.clock.time += t_sleep
            # OJO -> ESTO SOLO SERA VALIDO SI EL MANAGER ES V_MANAGER.
            #print(f' <<< clock.time = {self.clock.time}')

            # EXECUTE NEXT CYCLE
            if self.clock.time == self.time_next:  # now lambdas are optional
                self.lambdaf()
            self.deltfcn()
            self._execute_transducers()
            self.clear()

            t_a_sleep = rt_time.time()
            #print(f' <->-<-> Tiempo a m & deltas = {t_a_sleep}')
