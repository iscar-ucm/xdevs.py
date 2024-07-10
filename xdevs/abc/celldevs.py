from abc import ABC, abstractmethod
from typing import Generic
from xdevs import INFINITY
from xdevs.models import Port
from xdevs.celldevs import C, S


class DelayedOutput(Generic[C, S], ABC):
    def __init__(self, cell_id: C, serve: bool = False):
        """
        Cell-DEVS delayed output port. This is an abstract base class.
        :param cell_id: ID of the cell that owns this delayed output.
        :param serve: set to True if the port is going to be accessible via RPC server. Defaults to False.
        """
        from xdevs.celldevs.inout import CellMessage
        self.cell_id = cell_id
        self.port: Port[CellMessage[C, S]] = Port(CellMessage, 'out_celldevs', serve)

    @abstractmethod
    def add_to_buffer(self, when: float, state: S):
        """
        Schedules a cell state to send events.
        :param when: time at which the events must be sent.
        :param state: cell state. Events will be obtained by mapping this state.
        """
        pass

    @abstractmethod
    def next_time(self) -> float:
        """:return: next time at which events must be sent."""
        pass

    @abstractmethod
    def next_state(self) -> S:
        """:return: next cell state used to generate events."""
        pass

    @abstractmethod
    def pop_state(self):
        """removes schedule state from the delayed output."""
        pass

    def send_events(self, time: float):
        """
        If there is an scheduled state, it sends a new event via every Cell-DEVS output port.
        :param time: current simulation time.
        """
        from xdevs.celldevs.inout import CellMessage
        if self.next_time() <= time:
            self.port.add(CellMessage(self.cell_id, self.next_state()))

    def clean(self, time: float):
        """
        It cleans all the outdated scheduled cell states.
        :param time: current simulation time.
        """
        while self.next_time() < INFINITY and self.next_time() <= time:
            self.pop_state()
