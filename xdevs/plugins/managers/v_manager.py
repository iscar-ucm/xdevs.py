import queue
from typing import Callable

from xdevs.simRt.ManagerRt import ManagerRt

class Vmanager(ManagerRt):

    def __int__(self, **kwargs):
        super().__init__(**kwargs)

    def sleep(self, t_sleep) -> tuple[float, list[tuple[str, str]]]:
        return t_sleep, []

    def initialize(self):
        pass

    def add_event_handler(self, handler: Callable[[queue.SimpleQueue], None]):
        print('This manager does not accept any msgs')
