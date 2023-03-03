import queue
import time as rt_time
from typing import Any, Callable

from xdevs.simRt.ManagerRt import ManagerRt


class RtManager(ManagerRt):

    def __init__(self, **kwargs):
        self.t_a = 0
        self.total_delayed_t: float = 0
        self.lock = True
        self.error = 0
        super().__init__(**kwargs)

    def first_or_n_iteration(self, t_sleep):
        self.lock = False
        return t_sleep * self.time_scale

    def sleep(self, t_sleep: float) -> tuple[float, list[tuple[str, Any]]]:

        #print(f' >>> t_a = {self.t_a}')

        if self.lock:
            r_sleep = self.first_or_n_iteration(t_sleep)
        else:
            r_sleep = t_sleep * self.time_scale - (rt_time.time() - self.t_a) - self.total_delayed_t
            #print(f' >>> t_e = {rt_time.time() - self.t_a}')

        #print(f' >>> r_sleep = {r_sleep}')

        if r_sleep < 0:
            self.total_delayed_t = -r_sleep
            r_sleep = 0
            if self.total_delayed_t > self.max_delay:  # too much delay -> stop execution
                raise RuntimeError('ERROR: to much delayed time ')
        else:  # Sleep is positive. time elapsed and delayed_time are small. Everything went well
            self.total_delayed_t = 0

        #print(f' >>> total_delayed_t = {self.total_delayed_t}')

        t_busqueda = rt_time.time()
        try:
            port_name, msg = self.queue.get(timeout=r_sleep)
            slept = (rt_time.time() - t_busqueda)
            #print(f'>> slept = {slept} = {r_sleep} - ({rt_time.time()}-{t_busqueda})')
            #print('<<< MSG >>>')
            self.t_a = rt_time.time()
            return slept, [(port_name, msg)]
        except queue.Empty:
            slept = rt_time.time() - t_busqueda
            #print(f' No hay mensajes: r_sleep = {r_sleep} y el tiempo que ha tardado .time() - t_busqueda = {rt_time.time() - t_busqueda}')
            self.error += (slept - r_sleep)
            #print(f' Error = {slept - r_sleep} Error acumulado = {self.error}')
            #print(f'>> slept = {slept}')
            #print('<<< NO MSG >>>')
            self.t_a = rt_time.time()
            return slept, []
