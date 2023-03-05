import queue
import time as rt_time
from typing import Any, Callable

from xdevs.sim_rt.manager import AbstractRTManager


class RtManager(AbstractRTManager):

    def __init__(self, **kwargs):
        self.time_scale: float = kwargs.get('time_scale')
        self.max_delay: float = kwargs.get('max_delay')
        if self.max_delay < 0:
            raise Exception('Negative delay is not valid.')
        self.baseline_r_time = 0
        self.total_delayed_t: float = 0
        self.error = 0
        self.last_r_time = 0
        super().__init__(**kwargs)

    def initialize(self, initial_t):
        super().initialize(initial_t)
        print(f' <<< last_v_time = {self.last_v_time}')
        self.baseline_r_time = rt_time.time()
        self.last_r_time = self.baseline_r_time

    def sleep(self, next_v_time) -> tuple[float, list[tuple[str, Any]]]:
        next_r_time = self.last_r_time + (next_v_time - self.last_v_time) * self.time_scale
        # print(f' + next_r_time = {next_r_time}')
        try:
            if next_r_time - rt_time.time() > 0:
                port_name, msg = self.queue.get(timeout=next_r_time - rt_time.time())
                r_time = min(next_r_time, rt_time.time())
                v_time = (r_time - self.baseline_r_time) / self.time_scale
                self.last_v_time = v_time
                self.last_r_time = r_time
                return v_time, [(port_name, msg)]
            return next_v_time, []
        except queue.Empty:
            self.last_v_time = next_v_time
            self.last_r_time = next_r_time
            return next_v_time, []

    def exit(self, final_t: float):

        print(f' ¿tiempo ejecutado?  =  {rt_time.time() - self.baseline_r_time}')
        print(f' final_t? = {final_t * self.time_scale}')
        print(f' max_delay = {self.max_delay*self.time_scale}')
        print(f' error acumulado = {self.error}')

        if rt_time.time() - self.baseline_r_time - (final_t * self.time_scale) > (self.max_delay*self.time_scale):
            self.error += rt_time.time() - self.baseline_r_time - (final_t * self.time_scale)
            raise Exception('Too much delay.')
        pass
