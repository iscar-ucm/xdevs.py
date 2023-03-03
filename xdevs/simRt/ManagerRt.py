import queue
import threading
from abc import ABC, abstractmethod
from typing import Callable, Any


class ManagerRt(ABC):
    def __init__(self, **kwargs):
        self.last_v_time: float = 0
        self.time_scale: float = kwargs.get('time_scale')  # TODO
        self.max_delay: float = kwargs.get('max_delay')  # TODO
        if self.max_delay < 0:
            raise Exception('Negative delay is not valid.')
        self.event_handlers = list()
        self.threads = list()
        # self.event_handler: Callable[[queue.SimpleQueue], None] = kwargs.get('event_handler')

        self.queue = queue.SimpleQueue()

    # todo hacer clase event_handler
    def add_event_handler(self, handler: Callable[[queue.SimpleQueue], None]):
        self.event_handlers.append(handler)

    @abstractmethod
    def sleep(self, t_until: float) -> tuple[float, list[tuple[Any, Any]]]:
        """
        Simulates the time of the simulation of the DEVS model.
        time will be the instant the manager must sleep at most.
        It returns a float that will be the time until it actually slept.
        It returns a [], that contains the port_name and the msg.
        """
        pass

    def initialize(self):
        """ Executes any required action before starting simulation. """
        if self.event_handlers is None:  # TODO
            raise Exception('No handlers available.')
        for handler in self.event_handlers:
            t = threading.Thread(daemon=True, target=handler, args=[self.queue])
            t.start()
            self.threads.append(t)

    def exit(self, final_t: float):
        """ Executes any required action after complete simulation. """
        self.last_v_time = final_t
