from __future__ import annotations
import queue
import sys
import threading
import time
from typing import Any
from xdevs.models import Port
from xdevs.rt_sim.input_handler import InputHandler, InputHandlers
from xdevs.rt_sim.output_handler import OutputHandler, OutputHandlers


def run_handler(handler: InputHandler | OutputHandler):
    handler.initialize()
    try:
        handler.run()
    except Exception:  # TODO try to narrow this catch
        handler.exit()
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

        self.threads = list()
        # Queue for processing the external events that are being injecting in the system
        self.input_queue: queue.SimpleQueue = queue.SimpleQueue()
        # Lists for storing any handler
        self.input_handlers: list[InputHandler] = list()
        self.output_handlers: list[OutputHandler] = list()

    def add_input_handler(self, handler_id: str, **kwargs):
        """
        Add a new InputHandler to the system.

        :param handler_id: unique ID of the input handler to be created.
        :param kwargs: any additional configuration parameter needed for creating the input handler.
        """
        i_handler = InputHandlers.create_input_handler(handler_id, **kwargs, queue=self.input_queue)
        self.input_handlers.append(i_handler)

    def add_output_handler(self, handler_id: str, **kwargs):
        """
        Add a new OutputHandler to the system.

        :param handler_id: unique ID of the output handler to be created.
        :param kwargs: any additional configuration parameter needed for creating the output handler.
        """
        o_handler = OutputHandlers.create_output_handler(handler_id, **kwargs)
        self.output_handlers.append(o_handler)

    def initialize(self, initial_t: float):
        """
        Initialize function of the real time manager.
        It is responsible for creating and starting any handler in the handler's list.

        :param initial_t: initial time of the simulation.
        """
        for handlers in self.input_handlers, self.output_handlers:
            for handler in handlers:
                thread = threading.Thread(daemon=True, target=run_handler, args=[handler])
                thread.start()
                self.threads.append(thread)
        self.last_v_time = initial_t
        self.initial_r_time = time.time()
        self.last_r_time = self.initial_r_time

    def exit(self, final_t: float):
        self.last_v_time = final_t

    def sleep(self, next_v_time: float) -> tuple[float, list[tuple[Any, Any]]]:
        """
        Function that implements the real time specification by waiting for ingoing events to the system.

        :param next_v_time: simulation time of the next cycle.
        :return: a tuple of: actual simulation time when function returned and list of ingoing events.
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

    def output_messages(self, port: Port):
        """
        An outgoing event is inserted in the queues of all OutputHandlers.

        :param port: output port of the topmost DEVS model under simulation.
        """
        for o_handler in self.output_handlers:
            for msg in port.values:
                o_handler.queue.put((port.name, msg))
