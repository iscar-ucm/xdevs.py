from __future__ import annotations

from abc import ABC
from typing import Any
from xdevs.models import Atomic, Coupled, Port
from xdevs.sim import Coordinator
from .pystone import pystones


class DelayedAtomic(Atomic):
    def __init__(self, name: str, int_delay: float, ext_delay: float, test: bool = False):
        super().__init__(name)

        self.int_delay: float = int_delay
        self.ext_delay: float = ext_delay
        self.n_internals: int = 0
        self.n_externals: int = 0
        self.n_events: int = 0
        self.test: bool = test

        self.i_in: Port[int] = Port(int, "i_in")
        self.o_out: Port[int] = Port(int, "o_out")
        self.add_in_port(self.i_in)
        self.add_out_port(self.o_out)

    def deltint(self):
        if self.int_delay:
            pystones(self.int_delay)
        if self.test:
            self.n_internals += 1
        self.passivate()

    def deltext(self, e: Any):
        if self.ext_delay:
            pystones(self.ext_delay)
        if self.test:
            self.n_externals += 1
            self.n_events += len(self.i_in)
        self.activate()

    def lambdaf(self):
        self.o_out.add(0)

    def initialize(self):
        self.passivate()

    def exit(self):
        pass


class AbstractDEVStone(Coupled, ABC):
    def __init__(self, name: str, width: int, depth: int, int_delay: float, ext_delay: float, test: bool = False):
        super().__init__(name)
        if width < 1:
            raise ValueError("Invalid width")
        if depth < 1:
            raise ValueError("Invalid depth")
        if int_delay < 0:
            raise ValueError("Invalid int_delay")
        if ext_delay < 0:
            raise ValueError("Invalid ext_delay")

        self.depth: int = depth
        self.width: int = width
        self.int_delay: float = int_delay
        self.ext_delay: float = ext_delay

        self.i_in: Port[int] = Port(int, "i_in")
        self.o_out: Port[int] = Port(int, "o_out")
        self.add_in_port(self.i_in)
        self.add_out_port(self.o_out)

        self.coupled: AbstractDEVStone | None = None
        if depth == 1:
            atomic = DelayedAtomic("Atomic_0_0", int_delay, ext_delay, test)
            self.add_component(atomic)
            self.add_coupling(self.i_in, atomic.i_in)
            self.add_coupling(atomic.o_out, self.o_out)

    @property
    def n_atomics(self) -> int:
        res = 0 if self.coupled is None else self.coupled.n_atomics - 1
        return res + len(self.components)

    @property
    def n_eics(self) -> int:
        res = 0 if self.coupled is None else self.coupled.n_eics
        return res + sum(len(x) for x in self.eic.values())

    @property
    def n_ics(self) -> int:
        res = 0 if self.coupled is None else self.coupled.n_ics
        return res + sum(len(x) for x in self.ic.values())

    @property
    def n_eocs(self) -> int:
        res = 0 if self.coupled is None else self.coupled.n_eocs
        return res + sum(len(x) for x in self.eoc.values())

    @property
    def n_internals(self) -> int:
        return sum(x.n_internals for x in self.components)

    @property
    def n_externals(self) -> int:
        return sum(x.n_externals for x in self.components)

    @property
    def n_events(self) -> int:
        return sum(x.n_events for x in self.components)


class LI(AbstractDEVStone):
    def __init__(self, name: str, width: int, depth: int, int_delay: float, ext_delay: float, test: bool = False):
        super().__init__(name, width, depth, int_delay, ext_delay, test)
        if depth > 1:
            self.coupled = LI("Coupled_%d" % (self.depth - 1), self.width, self.depth - 1, self.int_delay, self.ext_delay, test)
            self.add_component(self.coupled)
            self.add_coupling(self.i_in, self.coupled.i_in)
            self.add_coupling(self.coupled.o_out, self.o_out)
            for idx in range(width - 1):
                atomic = DelayedAtomic("Atomic_%d_%d" % (idx, depth - 1), int_delay, ext_delay, test)
                self.add_component(atomic)
                self.add_coupling(self.i_in, atomic.i_in)


class HI(AbstractDEVStone):
    def __init__(self, name: str, width: int, depth: int, int_delay: float, ext_delay: float, test: bool = False):
        super().__init__(name, width, depth, int_delay, ext_delay, test)
        if depth > 1:
            self.coupled = HI("Coupled_%d" % (self.depth - 1), self.width, self.depth - 1, self.int_delay, self.ext_delay, test)
            self.add_component(self.coupled)
            self.add_coupling(self.i_in, self.coupled.i_in)
            self.add_coupling(self.coupled.o_out, self.o_out)
            prev_atomic = None
            for idx in range(width - 1):
                atomic = DelayedAtomic("Atomic_%d_%d" % (idx, depth - 1), int_delay, ext_delay, test)
                self.add_component(atomic)
                self.add_coupling(self.i_in, atomic.i_in)
                if prev_atomic is not None:
                    self.add_coupling(prev_atomic.o_out, atomic.i_in)
                prev_atomic = atomic


class HO(AbstractDEVStone):
    def __init__(self, name: str, width: int, depth: int, int_delay: float, ext_delay: float, test: bool = False):
        super().__init__(name, width, depth, int_delay, ext_delay, test)

        self.i_in2: Port[int] = Port(int, "i_in2")
        self.o_out2: Port[int] = Port(int, "o_out2")
        self.add_in_port(self.i_in2)
        self.add_out_port(self.o_out2)

        if depth > 1:
            self.coupled = HO("Coupled_%d" % (self.depth - 1), self.width, self.depth - 1, self.int_delay, self.ext_delay, test)
            self.add_component(self.coupled)
            self.add_coupling(self.i_in, self.coupled.i_in)
            self.add_coupling(self.i_in, self.coupled.i_in2)
            self.add_coupling(self.coupled.o_out, self.o_out)
            prev_atomic = None
            for idx in range(width - 1):
                atomic = DelayedAtomic("Atomic_%d_%d" % (idx, depth - 1), int_delay, ext_delay, test)
                self.add_component(atomic)
                self.add_coupling(self.i_in2, atomic.i_in)
                if prev_atomic is not None:
                    self.add_coupling(prev_atomic.o_out, atomic.i_in)
                self.add_coupling(atomic.o_out, self.o_out2)
                prev_atomic = atomic


class HOmod(AbstractDEVStone):
    def __init__(self, name: str, width: int, depth: int, int_delay: float, ext_delay: float, test: bool = False):
        super().__init__(name, width, depth, int_delay, ext_delay, test)

        self.i_in2: Port[int] = Port(int, "i_in2")
        self.add_in_port(self.i_in2)

        if depth > 1:
            self.coupled = HOmod("Coupled_%d" % (self.depth - 1), self.width, self.depth - 1, self.int_delay, self.ext_delay, test)
            self.add_component(self.coupled)
            self.add_coupling(self.i_in, self.coupled.i_in)
            self.add_coupling(self.coupled.o_out, self.o_out)

            prev_row, current_row = list(), list()
            # First row of atomics
            for i in range(1, width):
                atomic = DelayedAtomic("Atomic_(1,%d)_%d" % (i, depth - 1), int_delay, ext_delay, test)
                self.add_component(atomic)
                self.add_coupling(self.i_in2, atomic.i_in)
                self.add_coupling(atomic.o_out, self.coupled.i_in2)
                prev_row.append(atomic)
            # Second row of atomics
            for i in range(1, width):
                atomic = DelayedAtomic("Atomic_(2,%d)_%d" % (i, depth - 1), int_delay, ext_delay, test)
                self.add_component(atomic)
                if i == 1:
                    self.add_coupling(self.i_in2, atomic.i_in)
                for prev_atomic in prev_row:
                    self.add_coupling(atomic.o_out, prev_atomic.i_in)
                current_row.append(atomic)
            # Rest of the tree
            for layer in range(3, width + 1):
                prev_row = current_row
                current_row = list()
                for i in range(1, len(prev_row)):
                    atomic = DelayedAtomic("Atomic_(%d,%d)_%d" % (layer, i, depth - 1), int_delay, ext_delay, test)
                    self.add_component(atomic)
                    if i == 1:
                        self.add_coupling(self.i_in2, atomic.i_in)
                    self.add_coupling(atomic.o_out, prev_row[i].i_in)
                    current_row.append(atomic)


class Seeder(Atomic):
    def __init__(self, name: str):
        super().__init__(name)
        self.o_out: Port[int] = Port(int, "o_out")
        self.add_out_port(self.o_out)

    def deltint(self):
        self.passivate()

    def deltext(self, e: Any):
        self.passivate()

    def lambdaf(self):
        self.o_out.add(0)

    def initialize(self):
        self.activate()

    def exit(self):
        pass


class DEVStone(Coupled):
    def __init__(self, name: str, model_type: str, width: int, depth: int,
                 int_delay: float, ext_delay: float, test: bool = False):
        super().__init__(name)
        self.seeder: Seeder = Seeder("seeder")
        self.add_component(self.seeder)
        self.devstone: AbstractDEVStone
        if model_type == "LI":
            self.devstone = LI('root_LI', width, depth, int_delay, ext_delay, test)
        elif model_type == "HI":
            self.devstone = HI('root_HI', width, depth, int_delay, ext_delay, test)
        elif model_type == "HO":
            self.devstone = HO('root_HO', width, depth, int_delay, ext_delay, test)
        elif model_type == "HOmod":
            self.devstone = HOmod('root_HOmod', width, depth, int_delay, ext_delay, test)
        else:
            raise ValueError('unknown DEVStone model type')
        self.add_component(self.devstone)
        for port in self.devstone.in_ports:
            self.add_coupling(self.seeder.o_out, port)

    @property
    def n_atomics(self) -> int:
        return self.devstone.n_atomics

    @property
    def n_eics(self) -> int:
        return self.devstone.n_eics

    @property
    def n_ics(self) -> int:
        return self.devstone.n_ics

    @property
    def n_eocs(self) -> int:
        return self.devstone.n_eocs

    @property
    def n_internals(self) -> int:
        return self.devstone.n_internals

    @property
    def n_externals(self) -> int:
        return self.devstone.n_externals

    @property
    def n_events(self) -> int:
        return self.devstone.n_events


if __name__ == '__main__':
    import sys
    sys.setrecursionlimit(10000)
    root = HO("HO_root", 50, 50, 0, 0)
    coord = Coordinator(root)
    coord.initialize()
    coord.inject(root.i_in, 0)
    coord.simulate()
