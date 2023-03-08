from __future__ import annotations

import queue
import threading
import time
from typing import Callable, Any


class RealTimeManager:
    def __init__(self, max_jitter: float = None, time_scale: float = 1, event_window: float = 0):
        """
        TODO documentation
        :param max_jitter:
        :param time_scale:
        :param event_window:
        """
        if max_jitter is not None and max_jitter < 0:
            raise ValueError('negative max_jitter is not valid.')
        self.max_jitter: float | None = max_jitter
        if time_scale <= 0:
            raise ValueError('negative or zero time_scale is not valid.')
        self.time_scale: float = time_scale
        if event_window < 0:
            raise ValueError('negative event_window is not valid.')
        self.event_window: float = event_window

        self.initial_r_time: float = 0
        self.last_r_time: float = 0
        self.last_v_time: float = 0

        self.event_handlers = list()
        self.threads = list()
        self.queue = queue.SimpleQueue()

    # TODO hacer clases InputHandler y OutputHandler
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
        It returns a list that contains tuples with destination port name and the received msg.
        """
        next_r_time = self.last_r_time + (next_v_time - self.last_v_time) * self.time_scale
        events: list[tuple[str, Any]] = list()
        try:
            # First, we wait for a single message
            events.append(self.queue.get(timeout=max(next_r_time - time.time(), 0)))
            # Only if we receive one message will we wait for an additional event time window
            t_window = min(time.time() + self.event_window, next_r_time)
            while True:
                try:
                    events.append(self.queue.get(timeout=max(t_window - time.time(), 0)))
                except queue.Empty:
                    break  # event window timeout, we are done with messages
            # Finally, we compute the current time. Must be between last_r_time and next_r_time
            r_time = min(next_r_time, time.time())
            v_time = (r_time - self.initial_r_time) / self.time_scale
            self.last_v_time = v_time
            self.last_r_time = r_time
        except queue.Empty:
            # we did not receive any message, just update the time
            self.last_v_time = next_v_time
            self.last_r_time = next_r_time
        # If needed, we check that the jitter is not too big
        if self.max_jitter is not None and abs(time.time() - self.last_r_time) > self.max_jitter:
            raise RuntimeError('maximum jitter exceeded.')
        return self.last_v_time, events
