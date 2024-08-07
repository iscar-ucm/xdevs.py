from __future__ import annotations
import inspect
import pickle
from abc import ABC, abstractmethod
from collections import deque, defaultdict
from typing import Generator, Generic, Iterator
from xdevs import PHASE_ACTIVE, PHASE_PASSIVE, INFINITY, T


class Port(Generic[T]):
    def __init__(self, p_type: type[T] | None = None, name: str = None, serve: bool = False):
        """
        xDEVS implementation of DEVS Port.
        :param p_type: data type of events to be sent/received via the new port instance.
        :param name: name of the new port instance. Defaults to the name of the port's class.
        :param serve: set to True if the port is going to be accessible via RPC server. Defaults to False.
        """
        self.name: str = name if name else self.__class__.__name__  # Name of the port
        self.p_type: type[T] | None = p_type  # Port type. If None, it can contain any type of event.
        self.serve: bool = serve                 # True if port is going to be accessible via RPC server
        self.parent: Component | None = None     # xDEVS Component that owns the port
        self._values: deque[T] = deque()         # Bag containing events directly written to the port
        self._bag: list[Port[T]] = list()        # Bag containing coupled ports containing events

    def __bool__(self) -> bool:
        return not self.empty()

    def __len__(self) -> int:
        return sum((len(port) for port in self._bag), len(self._values))

    def __str__(self) -> str:
        p_type = self.p_type.__name__ if self.p_type is not None else 'None'
        return f'{self.name}<{p_type}>'

    def __repr__(self) -> str:
        return str(self)

    def empty(self) -> bool:
        return not bool(self._values or self._bag)

    def clear(self):
        self._values.clear()
        self._bag.clear()

    @property
    def values(self) -> Generator[T, None, None]:
        """:return: Generator function that can iterate over all the values contained in the port."""
        for val in self._values:
            yield val
        for port in self._bag:
            for val in port.values:
                yield val

    def get(self) -> T:
        """
        :return: first value in the port.
        :raises StopIteration: if port is empty.
        """
        return next(self.values)

    def add(self, val: T):
        """
        Adds a new value to the local value bag of the port.
        :param val: event to be added.
        :raises TypeError: If event is not instance of port type.
        """
        if self.p_type is not None and not isinstance(val, self.p_type):
            raise TypeError(f'Value type is {type(val).__name__} ({self.p_type.__name__} expected)')
        self._values.append(val)

    def extend(self, vals: Iterator[T]):
        """
        Adds a set of new values to the local value bag of the port.
        :param vals: list containing all the values to be added.
        :raises TypeError: If one of the values is not instance of port type.
        """
        for val in vals:
            self.add(val)

    def add_to_bag(self, port: Port[T]):
        """
        Adds a port that contains events to the message bag.
        :param port: port to be added to the bag.
        """
        if port:
            self._bag.append(port)


class Component(ABC):
    def __init__(self, name: str = None):
        """
        Abstract Base Class for an xDEVS model.
        :param name: name of the xDEVS model. Defaults to the name of the component's class.
        """
        self.name: str = name if name else self.__class__.__name__
        self.parent: Coupled | None = None # Parent component of this component
        self.input: dict[str, Port] = dict()  # Dictionary containing all the component's input ports by name
        self.output: dict[str, Port] = dict() # Dictionary containing all the component's output ports by name
        # TODO make these lists private
        self.in_ports: list[Port] = list()   # List containing all the component's input ports (serialized for performance)
        self.out_ports: list[Port] = list()  # List containing all the component's output ports (serialized for performance)

    def __str__(self) -> str:
        in_str = " ".join([p.name for p in self.in_ports])
        out_str = " ".join([p.name for p in self.out_ports])
        return f'{self.name}: InPorts[{in_str}] OutPorts[{out_str}]'

    def __repr__(self):
        return self.name

    @abstractmethod
    def initialize(self):
        """This method is executed before starting a simulation."""
        pass

    @abstractmethod
    def exit(self):
        """This method is executed after finishing a simulation."""
        pass

    def in_empty(self) -> bool:
        """:return: True if model has not any message in all its input ports."""
        return not any(self.in_ports)

    def out_empty(self) -> bool:
        """:return: True if model has not any message in all its output ports."""
        return not any(self.out_ports)

    @property
    def used_in_ports(self) -> Generator[Port, None, None]:
        return (port for port in self.in_ports if port)

    @property
    def used_out_ports(self) -> Generator[Port, None, None]:
        return (port for port in self.out_ports if port)

    def add_in_port(self, port: Port):
        """
        Adds an input port to the xDEVS model.
        :param port: port to be added to the model.
        :panics NameError: if port name already exists.
        """
        if port.name in self.input:
            raise NameError("Input port name already exists")
        port.parent = self
        self.input[port.name] = port
        self.in_ports.append(port)

    def add_out_port(self, port: Port):
        """
        Adds an output port to the xDEVS model
        :param port: port to be added to the model.
        :panics NameError: if port name already exists.
        """
        if port.name in self.output:
            raise ValueError("Output port name already exists")
        port.parent = self
        self.output[port.name] = port
        self.out_ports.append(port)

    def get_in_port(self, name) -> Port | None:
        """:return: Input port with the given name. If port is not found, returns None."""
        return self.input.get(name)

    def get_out_port(self, name) -> Port | None:
        """:return: Output port with the given name. If port is not found, returns None."""
        return self.output.get(name)


class Coupling(Generic[T]):
    def __init__(self, port_from: Port[T], port_to: Port[T], host=None):
        """
        xDEVS implementation of DEVS couplings.
        :param port_from: DEVS transmitter port.
        :param port_to: DEVS receiver port.
        :param host: TODO documentation for this
        :raises ValueError: port types are incompatible.
        """
        # Check that couplings are valid
        if port_from.p_type is not None and port_to.p_type is not None and port_to in inspect.getmro(port_from.p_type):
            raise ValueError("Ports don't share the same port type")

        self.port_from: Port = port_from
        self.port_to: Port = port_to
        self.host = host  # TODO identify host's variable type

    def __str__(self) -> str:
        return f"({self.port_from} -> {self.port_to})"

    def __repr__(self) -> str:
        return str(self)

    def propagate(self):
        """Copies messages from the transmitter port to the receiver port"""
        if self.host:
            if self.port_from:
                values = list(map(lambda x: pickle.dumps(x, protocol=0).decode(), self.port_from.values))
                self.host.inject(self.port_to, values)
        else:
            self.port_to.add_to_bag(self.port_from)


class Atomic(Component, ABC):
    def __init__(self, name: str = None):
        """
        xDEVS implementation of DEVS Atomic Model.
        :param name: name of the atomic model. If no name is provided, it will take the class's name by default.
        """
        super().__init__(name)

        self.phase: str = PHASE_PASSIVE
        self.sigma: float = INFINITY

    def ta(self) -> float:
        """:return: remaining time for the atomic model's internal transition."""
        return self.sigma

    def __str__(self) -> str:
        return f'{self.name}({self.phase}, {self.sigma})'

    @abstractmethod
    def deltint(self):
        """Describes the internal transitions of the atomic model."""
        pass

    @abstractmethod
    def deltext(self, e: float):
        """
        Describes the external transitions of the atomic model.
        :param e: elapsed time between last transition and the external transition.
        """
        pass

    @abstractmethod
    def lambdaf(self):
        """Describes the output function of the atomic model."""
        pass

    def deltcon(self):
        """Confluent transitions of the atomic model. By default, internal transition is triggered first."""
        self.deltint()
        self.deltext(0)

    def hold_in(self, phase: str, sigma: float):
        """
        Change atomic model's phase and next timeout.
        :param phase: atomic model's new phase.
        :param sigma: time remaining to the next timeout.
        """
        self.phase = phase
        self.sigma = sigma

    def activate(self, phase: str = PHASE_ACTIVE):
        """
        Sets next timeout to 0.
        :param phase: New phase. Defaults to "PHASE_ACTIVE".
        """
        self.phase = phase
        self.sigma = 0

    def passivate(self, phase: str = PHASE_PASSIVE):
        """
        Sets next timeout to infinity.
        :param phase: New phase. Defaults to "PHASE_PASSIVE".
        """
        self.phase = phase
        self.sigma = INFINITY

    def continuef(self, e: float):
        """
        Reduces the next timeout by e time units.
        :param e: elapsed time to be subtracted from sigma.
        """
        self.sigma -= e


class Coupled(Component, ABC):
    def __init__(self, name: str = None):
        """
        xDEVS implementation of DEVS Coupled Model.
        :param name: name of the coupled model. If no name is provided, it will take the class's name by default.
        """
        super().__init__(name)
        self.components: list[Component] = list()
        self.ic: dict[Port, dict[Port, Coupling]] = dict()
        self.eic: dict[Port, dict[Port, Coupling]] = dict()
        self.eoc: dict[Port, dict[Port, Coupling]] = dict()
        # TODO serialized versions of ic, eic and eoc for performance

    def initialize(self):
        pass

    def exit(self):
        pass

    def add_coupling(self, p_from: Port, p_to: Port, host=None):
        """
        Adds coupling between two submodules of the coupled model.
        :param p_from: DEVS transmitter port.
        :param p_to: DEVS receiver port.
        :param host: TODO documentation
        :raises ValueError: if coupling is not well defined.
        """
        if p_from.parent == self and p_to.parent in self.components:
            coupling_set = self.eic
        elif p_from.parent in self.components and p_to.parent == self:
            coupling_set = self.eoc
        elif p_from.parent in self.components and p_to.parent in self.components:
            coupling_set = self.ic
        else:
            raise ValueError("Components that compose the coupling are not submodules of coupled model")

        if p_from not in coupling_set:
            coupling_set[p_from] = dict()
        coupling_set[p_from][p_to] = Coupling(p_from, p_to, host)

    def remove_coupling(self, coupling: Coupling):
        """
        Removes coupling between two submodules of the coupled model.
        :param coupling: Couplings to be removed.
        :raises ValueError: if coupling is not found.
        """
        port_from = coupling.port_from
        port_to = coupling.port_to
        for coupling_set in (self.eic, self.eoc, self.ic):
            if coupling_set.get(port_from, dict()).pop(port_to, None) == coupling:
                if not coupling_set[port_from]:
                    coupling_set.pop(port_from)
                return
        raise ValueError("Coupling was not found in model definition")

    def add_component(self, component: Component):
        """
        Adds component to coupled model.
        :param component: component to be added to the Coupled model.
        """
        component.parent = self
        self.components.append(component)

    def flatten(self) -> tuple[list[Atomic], list[Coupling]]:
        """
        Flattens coupled model (i.e., parent coupled model inherits the connection of the model).
        :return: Components and couplings to be transferred to parent
        """
        new_comps_up: list[Atomic] = list()  # list with children components to be inherited by parent
        new_coups_up: list[Coupling] = list()  # list with couplings to be inherited by parent

        old_comps: list[Coupled] = list()  # list with children coupled models to be deleted

        for comp in self.components:
            if isinstance(comp, Coupled):  # Propagate flattening to children coupled models
                new_comps_down, new_coups_down = comp.flatten()
                old_comps.append(comp)
                for new_comp in new_comps_down:
                    self.add_component(new_comp)
                for coup in new_coups_down:
                    self.add_coupling(coup.port_from, coup.port_to, coup.host)
            elif isinstance(comp, Atomic):
                new_comps_up.append(comp)

        for comp in old_comps:
            self._remove_couplings_of_child(comp)
            self.components.remove(comp)

        if self.parent is not None:  # If module is not root, trigger the flatten process
            left_bridge_eic = self._create_left_bridge(self.parent.eic)
            new_coups_up.extend(self._complete_left_bridge(left_bridge_eic))

            left_bridge_ic = self._create_left_bridge(self.parent.ic)
            right_bridge_ic = self._create_right_bridge(self.parent.ic)
            new_coups_up.extend(self._complete_left_bridge(left_bridge_ic))
            new_coups_up.extend(self._complete_right_bridge(right_bridge_ic))

            right_bridge_eoc = self._create_right_bridge(self.parent.eoc)
            new_coups_up.extend(self._complete_right_bridge(right_bridge_eoc))

            new_coups_up.extend((c for cl in self.ic.values() for c in cl.values()))

        return new_comps_up, new_coups_up

    def _remove_couplings_of_child(self, child: Coupled):
        for in_port in child.in_ports:
            self._remove_couplings(in_port, self.eic)
            self._remove_couplings(in_port, self.ic)
        for out_port in child.out_ports:
            self._remove_couplings(out_port, self.ic)
            self._remove_couplings(out_port, self.eoc)

    @staticmethod
    def _remove_couplings(port: Port, couplings: dict[Port, dict[Port, Coupling]]):
        # Remove port from couplings list
        couplings.pop(port, None)
        # For remaining ports, remove couplings which source is the port to be removed
        for coups in couplings.values():
            coups.pop(port, None)
        return

    def _create_left_bridge(self, pc) -> dict[Port, list[Port]]:
        bridge = defaultdict(list)
        for in_port in self.in_ports:
            for port_from in pc:
                if in_port in pc[port_from]:
                    bridge[in_port].append(port_from)

        return bridge

    def _create_right_bridge(self, pc) -> dict[Port, list[Port]]:
        bridge = defaultdict(list)
        for out_port in self.out_ports:
            for port_from in pc:
                if port_from == out_port:
                    for port_to in pc[port_from]:
                        bridge[out_port].append(port_to)
        return bridge

    def _complete_left_bridge(self, bridge: dict[Port, list[Port]]) -> list[Coupling]:
        couplings = list()
        for coup_list in self.eic.values():
            for coup in coup_list.values():
                ports = bridge[coup.port_from]
                for port in ports:
                    couplings.append(Coupling(port, coup.port_to))
        return couplings

    def _complete_right_bridge(self, bridge: dict[Port, list[Port]]) -> list[Coupling]:
        couplings = list()
        for coup_list in self.eoc.values():
            for coup in coup_list.values():
                ports = bridge[coup.port_to]
                for port in ports:
                    couplings.append(Coupling(coup.port_from, port))
        return couplings
