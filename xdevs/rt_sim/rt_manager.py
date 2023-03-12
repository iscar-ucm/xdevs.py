from __future__ import annotations
import queue
import sys
import threading
import time
from typing import Any
from xdevs.rt_sim.input_handler import InputHandler, InputHandlers


def run_handler(i_handler: InputHandler):
    """"""
    i_handler.initialize()
    try:
        i_handler.run()
    except Exception:  # TODO try to narrow this catch
        i_handler.exit()
        sys.exit()


class RealTimeManager:
    def __init__(self, max_jitter: float = None, time_scale: float = 1, event_window: float = 0):
        """
        The RealTimeManager is responsible for collecting external events and implement real time in the simulation.

        :param max_jitter: Maximum delay time the system can absorb. Default is None (i.e., no jitter check)
        :param time_scale: Scale for increasing or decreasing the simulated time. Default is 1 s (i.e., no scale)
        :param event_window: Additional time is added to check for others events. Default is 0 (i.e., no window)
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

        self.input_handlers: list[InputHandler] = list()
        self.threads = list()
        self.input_queue = queue.SimpleQueue()

    def add_input_handler(self, handler_id: str, **kwargs):
        """
        TODO documentation

        :param handler_id:
        :param kwargs:
        :return:
        """
        i_handler = InputHandlers.create_input_handler(handler_id, **kwargs, queue=self.input_queue)
        self.input_handlers.append(i_handler)

    def initialize(self, initial_t: float):
        """
        TODO documentation

        :param initial_t:
        :return:
        """
        for handler in self.input_handlers:
            t = threading.Thread(daemon=True, target=run_handler, args=[handler])
            t.start()
            self.threads.append(t)
        self.last_v_time = initial_t
        self.initial_r_time = time.time()
        self.last_r_time = self.initial_r_time

    def exit(self, final_t: float):
        self.last_v_time = final_t

    def sleep(self, next_v_time: float) -> tuple[float, list[tuple[Any, Any]]]:
        """
        TODO documentation

        :param next_v_time:
        :return:
        """
        next_r_time = self.last_r_time + (next_v_time - self.last_v_time) * self.time_scale
        events: list[tuple[str, Any]] = list()
        try:
            # First, we wait for a single message
            events.append(self.input_queue.get(timeout=max(next_r_time - time.time(), 0)))
            # Only if we receive one message will we wait for an additional event time window
            t_window = min(time.time() + self.event_window, next_r_time)
            while True:
                try:
                    events.append(self.input_queue.get(timeout=max(t_window - time.time(), 0)))
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
