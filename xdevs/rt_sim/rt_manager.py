from __future__ import annotations

import queue
import threading
import time
from typing import Callable, Any


class RealTimeManager:
    def __init__(self, max_jitter: float = None, time_scale: float = 1):
        """
        TODO documentation
        :param max_jitter:
        :param time_scale:
        """
        if max_jitter is not None and max_jitter < 0:
            raise ValueError('negative maximum jitter is not valid.')
        self.max_jitter: float | None = max_jitter
        if time_scale <= 0:
            raise ValueError('negative or zero time_scale is not valid.')
        self.time_scale: float = time_scale

        self.initial_r_time: float = 0
        self.last_r_time: float = 0
        self.last_v_time: float = 0

        self.event_handlers = list()
        self.threads = list()
        self.queue = queue.SimpleQueue()

    # TODO hacer clase event_handler
    def add_event_handler(self, handler: Callable[[queue.SimpleQueue], None]):
        self.event_handlers.append(handler)

    def initialize(self, initial_t: float):
        for handler in self.event_handlers:
            t = threading.Thread(daemon=True, target=handler, args=[self.queue])
            t.start()
            self.threads.append(t)
        self.last_v_time = initial_t
        self.initial_r_time = time.time()
        self.last_r_time = self.initial_r_time

    def exit(self, final_t: float):
        self.last_v_time = final_t
        # TODO llamar al método exit de los handlers

    def sleep(self, next_v_time: float) -> tuple[float, list[tuple[Any, Any]]]:
        """
        Simulates the time of the simulation of the DEVS model.
        time will be the instant the manager must sleep at most.
        It returns a float that will be the time until it actually slept.
        It returns a [], that contains the port_name and the msg.
        """
        next_r_time = self.last_r_time + (next_v_time - self.last_v_time) * self.time_scale
        events: list[tuple[str, Any]] = list()
        try:
            events.append(self.queue.get(timeout=max(next_r_time - time.time(), 0)))  # first event has timeout
            while not self.queue.empty():  # if we reach this point, we make sure that we leave the queue empty
                events.append(self.queue.get())
            r_time = min(next_r_time, time.time())
            v_time = (r_time - self.initial_r_time) / self.time_scale
            self.last_v_time = v_time
            self.last_r_time = r_time
        except queue.Empty:
            self.last_v_time = next_v_time
            self.last_r_time = next_r_time
        if self.max_jitter is not None and abs(time.time() - self.last_r_time) > self.max_jitter:
            raise RuntimeError('maximum jitter exceeded.')
        return self.last_v_time, events
