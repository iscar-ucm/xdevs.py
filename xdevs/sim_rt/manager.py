import queue
import threading
from typing import Callable, Any


class AbstractRTManager:
    def __init__(self, **kwargs):
        self.last_v_time: float = 0
        self.event_handlers = list()
        self.threads = list()
        # self.event_handler: Callable[[queue.SimpleQueue], None] = kwargs.get('event_handler')
        self.queue = queue.SimpleQueue()

    # todo hacer clase event_handler
    def add_event_handler(self, handler: Callable[[queue.SimpleQueue], None]):
        self.event_handlers.append(handler)

    def sleep(self, t_until: float) -> tuple[float, list[tuple[Any, Any]]]:
        """
        Simulates the time of the simulation of the DEVS model.
        time will be the instant the manager must sleep at most.
        It returns a float that will be the time until it actually slept.
        It returns a [], that contains the port_name and the msg.
        """
        self.last_v_time = t_until
        return self.last_v_time, []

    def initialize(self, initial_t: float):
        """ Executes any required action before starting simulation. """
        # TODO
        # if self.event_handlers is None:
        #   raise Exception('No handlers available.')
        self.last_v_time = initial_t
        for handler in self.event_handlers:
            t = threading.Thread(daemon=True, target=handler, args=[self.queue])
            t.start()
            self.threads.append(t)

    def exit(self, final_t: float):
        """ Executes any required action after complete simulation. """
        self.last_v_time = final_t
