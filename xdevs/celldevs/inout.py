from __future__ import annotations
from typing import ClassVar, Dict, Generic, Optional, Type, Callable, Any
from xdevs.models import Port
from xdevs.abc.transducer import Transducible, T
from xdevs.celldevs import C, S


class CellMessage(Transducible, Generic[C, S]):

    state_t: ClassVar[Type[S]] = None

    def __init__(self, cell_id: C, cell_state: S):
        self.cell_id = cell_id
        self.cell_state = cell_state

    @classmethod
    def transducer_map(cls) -> dict[str, tuple[Type[T], Callable[[Any], T]]]:
        if issubclass(cls.state_t, Transducible):
            res = {'cell_id': (str, lambda x: x.cell_id)}
            for field, (t, l) in cls.state_t.transducer_map().items():
                res[field] = (t, lambda x: l(x.cell_state))
            return res
            # return {
            #    'cell_id': (str, lambda x: x.cell_id),
            #     **{field: (t, lambda x: l(x.cell_state)) for field, (t, l) in cls.state_t.transducer_map().items()}
            #}
        return {
            'cell_id': (str, lambda x: x.cell_id),
            'cell_state': (str, lambda x: x.cell_state),
        }

class InPort(Generic[C, S]):
    def __init__(self, serve: bool = False):
        """
        Cell-DEVS in port.
        :param serve: set to True if the port is going to be accessible via RPC server. Defaults to False.
        """
        self.port: Port[CellMessage[C, S]] = Port(CellMessage, 'in_celldevs', serve)
        self.history: Dict[C, S] = dict()

    def read_new_events(self):
        """It stores the latest incoming events into self.history"""
        for cell_message in self.port.values:
            self.history[cell_message.cell_id] = cell_message.cell_state

    def get(self, cell_id: C) -> Optional[S]:
        """
        Returns latest received event.
        :param cell_id: ID of the cell that sent the event.
        :return: latest received event. If no event has been received, it returns None.
        """
        return self.history.get(cell_id)
