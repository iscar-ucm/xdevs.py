from __future__ import annotations
from typing import Generic
from xdevs.abc.celldevs import C, S, DelayedOutput, INFINITY


class InertialDelayedOutput(DelayedOutput[C, S], Generic[C, S]):
    def __init__(self, cell_id: C, serve: bool = False):
        super().__init__(cell_id, serve)
        self.last_state: S | None = None
        self.next_t: float = INFINITY

    def add_to_buffer(self, when: float, state: S):
        self.next_t, self.last_state = when, state

    def next_time(self) -> float:
        return self.next_t

    def next_state(self) -> S:
        return self.last_state

    def pop_state(self):
        self.next_t = INFINITY
