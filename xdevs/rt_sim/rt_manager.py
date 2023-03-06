import queue
import threading
from typing import Callable, Any
import time as rt_time


class RtManager:
    def __init__(self, **kwargs):
        self.time_scale: float = kwargs.get('time_scale')
        if self.time_scale <= 0:
            raise Exception('Negative or zero time_scale is not valid.')
        self.max_delay: float = kwargs.get('max_delay')
        if self.max_delay < 0:
            raise Exception('Negative delay is not valid.')

        self.baseline_r_time = 0
        self.error = 0
        self.last_r_time = 0
        self.last_v_time: float = 0

        self.event_handlers = list()
        self.threads = list()
        # self.event_handler: Callable[[queue.SimpleQueue], None] = kwargs.get('event_handler')
        self.queue = queue.SimpleQueue()

    # todo hacer clase event_handler
    def add_event_handler(self, handler: Callable[[queue.SimpleQueue], None]):
        self.event_handlers.append(handler)

    def sleep(self, next_v_time: float) -> tuple[float, list[tuple[Any, Any]]]:
        """
        Simulates the time of the simulation of the DEVS model.
        time will be the instant the manager must sleep at most.
        It returns a float that will be the time until it actually slept.
        It returns a [], that contains the port_name and the msg.
        """
        next_r_time = self.last_r_time + (next_v_time - self.last_v_time) * self.time_scale

        try:
            if next_r_time - rt_time.time() > 0:
                port_name, msg = self.queue.get(timeout=next_r_time - rt_time.time())
                r_time = min(next_r_time, rt_time.time())
                v_time = (r_time - self.baseline_r_time) / self.time_scale
                self.last_v_time = v_time
                self.last_r_time = r_time
                return v_time, [(port_name, msg)]
            print(f'TIMEOUT ERROR, resta-> {next_r_time - rt_time.time()}')
            print('-> r_time', next_r_time)
            print('-> .time', rt_time.time())
            return next_v_time, [] # en vez hacer, raise exception por .time > next_r_time ?

        except queue.Empty:
            self.last_v_time = next_v_time
            self.last_r_time = next_r_time

            if rt_time.time() - self.baseline_r_time - (next_v_time * self.time_scale) > (
                    self.max_delay * self.time_scale):
                raise Exception('Too much delay.')

            return next_v_time, []

    def initialize(self, initial_t: float):
        for handler in self.event_handlers:
            t = threading.Thread(daemon=True, target=handler, args=[self.queue])
            t.start()
            self.threads.append(t)
        self.last_v_time = initial_t
        self.baseline_r_time = rt_time.time()
        self.last_r_time = self.baseline_r_time

    def exit(self, final_t: float):
        self.last_v_time = final_t
        """
        print(f' ¿tiempo ejecutado?  =  {rt_time.time() - self.baseline_r_time}')
        print(f' final_t? = {final_t * self.time_scale}')
        print(f' max_delay = {self.max_delay*self.time_scale}')
        """
        if rt_time.time() - self.baseline_r_time - (final_t * self.time_scale) > (self.max_delay * self.time_scale):
            raise Exception('Too much delay.')
