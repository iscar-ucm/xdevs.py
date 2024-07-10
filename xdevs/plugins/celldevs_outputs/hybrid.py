from __future__ import annotations
from collections import deque
from typing import Deque, Generic
from xdevs.abc.celldevs import C, S, DelayedOutput, INFINITY


class HybridDelayedOutput(DelayedOutput[C, S], Generic[C, S]):
    def __init__(self, cell_id: C, serve: bool = False):
        super().__init__(cell_id, serve)
        self.last_state: S | None = None
        self.next_states: Deque[tuple[float, S]] = deque()

    def add_to_buffer(self, when: float, state: S):
        while self.next_states and self.next_states[-1][0] >= when:
            self.next_states.pop()
        self.next_states.append((when, state))

    def next_time(self) -> float:
        return INFINITY if not self.next_states else self.next_states[0][0]

    def next_state(self) -> S:
        return self.last_state if not self.next_states else self.next_states[0][1]

    def pop_state(self):
        if self.next_states:
            self.last_state = self.next_states.popleft()[1]
