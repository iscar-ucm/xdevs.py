from __future__ import annotations
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any, Generic
from xdevs.celldevs import C, S, V
from xdevs.celldevs.inout import CellMessage, InPort
from xdevs.models import Atomic
from xdevs.factory import DelayedOutputs, DelayedOutput


class CellConfig(Generic[C, S, V]):
    def __init__(self, config_id: str, c_type: type[C], s_type: type[S], v_type: type[V], **kwargs):
        """
        Cell-DEVS configuration structure.
        :param config_id: identifier of the configuration.
        :param c_type: type used to identify cells.
        :param s_type: type used to represent cell states.
        :param v_type: type used to represent vicinity between cells.
        :param cell_type: identifier of the cell type.
        :param delay: identifier of the delay buffer implemented by the cell. By default, it is set to inertial.
        :param config: any additional configuration parameters.
        :param state: parameters required to create the initial state of the cell.
        :param neighborhood: representation of the cell neighborhood. By default, it is empty.
        :param cell_map: list of cells that implement this configuration. By default, it is empty.
        :param eic: list of external input couplings. By default, it is empty.
        :param eoc: list of external output couplings. By default, it is empty.
        """
        self.config_id: str = config_id
        self.c_type: type[C] = c_type
        self.s_type: type[S] = s_type
        self.v_type: type[V] = v_type
        CellMessage.state_t = s_type

        self.cell_type: str = kwargs['cell_type']
        self.delay_type: str = kwargs.get('delay', 'inertial')
        self.cell_config = kwargs.get('config')
        self.state = kwargs.get('state')
        self.raw_neighborhood: list[dict] = kwargs.get('neighborhood', list())
        self.cell_map: list[C] | None = None if self.default else self._load_map(*kwargs.get('cell_map', list()))
        self.eic: list[tuple[str, str]] = self._parse_couplings(kwargs.get('eic', list()))
        self.ic: list[tuple[str, str]] = [('out_celldevs', 'in_celldevs')]
        self.eoc: list[tuple[str, str]] = self._parse_couplings(kwargs.get('eoc', list()))

    @property
    def default(self) -> bool:
        """:return: true if this configuration profile is the default one."""
        return self.config_id == 'default'

    def apply_patch(self, config_id: str, **kwargs):
        """
        Applies a configuration patch. This method is used for non-default configurations.
        :param config_id: configuration ID.
        :param cell_type: identifier of the cell type.
        :param delay: identifier of the delay buffer implemented by the cell. By default, it is set to inertial.
        :param config: any additional configuration parameters.
        :param state: parameters required to create the initial state of the cell.
        :param neighborhood: representation of the cell neighborhood. By default, it is empty.
        :param cell_map: list of cells that implement this configuration. By default, it is empty.
        :param eic: list of external input couplings. By default, it is empty.
        :param ic: list of internal couplings. By default, it is empty.  # TODO remove this?
        :param eoc: list of external output couplings. By default, it is empty.
        """
        self.config_id = config_id
        self.cell_type = kwargs.get('cell_type', self.cell_type)
        self.delay_type = kwargs.get('delay', self.delay_type)
        if 'config' in kwargs:
            self.cell_config = self._patch_dict(self.cell_config, kwargs['config']) \
                if isinstance(self.cell_config, dict) else kwargs['config']
        if 'state' in kwargs:
            self.state = self._patch_dict(self.state, kwargs['state']) \
                if isinstance(self.state, dict) else kwargs['state']
        self.raw_neighborhood = kwargs.get('neighborhood', self.raw_neighborhood)
        if 'cell_map' in kwargs:
            self.cell_map = self._load_map(*kwargs['cell_map'])
        if 'eic' in kwargs:
            self.eic = self._parse_couplings(kwargs['eic'])
        if 'ic' in kwargs:
            self.ic = self._parse_couplings(kwargs['ic'])
        if 'eoc' in kwargs:
            self.eoc = self._parse_couplings(kwargs['eoc'])

    def load_state(self) -> S:
        """:return: a new initial state structure."""
        return self._load_value(self.s_type, self.state)

    def load_neighborhood(self) -> dict[C, V]:
        """:return: a new neighborhood."""
        neighbors: dict[C, V] = dict()
        for neighborhood in self.raw_neighborhood:
            for neighbor, vicinity in neighborhood.items():
                neighbors[self.c_type(neighbor)] = self._load_vicinity(vicinity)
        return neighbors

    def _load_map(self, *args) -> list[C]:
        return [self.c_type(self.config_id)]

    def _load_vicinity(self, vicinity: Any):
        return self._load_value(self.v_type, vicinity)

    @classmethod
    def _patch_dict(cls, d: dict, patch: dict) -> dict:
        for k, v in patch.items():
            d[k] = cls._patch_dict(d[k], v) if isinstance(v, dict) and k in d and isinstance(d[k], dict) else v
        return d

    @staticmethod
    def _parse_couplings(couplings: list[list[str]]) -> list[tuple[str, str]]:
        return [(coupling[0], coupling[1]) for coupling in couplings]

    @staticmethod
    def _load_value(t_type, params: Any):
        params = deepcopy(params)
        if isinstance(params, dict):
            return t_type(**params)
        elif isinstance(params, list):
            return t_type(*params)
        elif params is not None:
            return t_type(params)
        return t_type()


class Cell(Atomic, ABC, Generic[C, S, V]):
    def __init__(self, cell_id: C, config: CellConfig[C, S, V]):
        """
        Abstract Base Class for a Cell-DEVS cell.
        :param cell_id: cell identifier.
        :param config: cell configuration structure.
        """
        super().__init__(str(cell_id))
        self._clock: float = 0
        self._config: CellConfig = config
        self.ics = config.eic
        self.cell_id: C = cell_id
        self.cell_state: S = config.load_state()
        self.neighborhood: dict[C, V] = self._load_neighborhood()

        self.in_celldevs: InPort[C, S] = InPort(self.cell_id)
        self.out_celldevs: DelayedOutput[C, S] = DelayedOutputs.create_delayed_output(config.delay_type, self.cell_id)
        self.add_in_port(self.in_celldevs.port)
        self.add_out_port(self.out_celldevs.port)

    @property
    def neighbors_state(self) -> dict[C, S]:
        return self.in_celldevs.history

    @abstractmethod
    def local_computation(self, cell_state: S) -> S:
        """
        Computes new cell state depending on its previous state.
        :param cell_state: current cell state.
        :return: new cell state.
        """
        pass

    @abstractmethod
    def output_delay(self, cell_state: S) -> float:
        """
        Returns delay to be applied to output messages related to new cell state.
        :param cell_state: new cell state.
        :return: delay to be applied.
        """
        pass

    def deltint(self):
        self._clock += self.sigma
        self.out_celldevs.clean(self._clock)
        self.sigma = self.out_celldevs.next_time() - self._clock

    def deltext(self, e: float):
        self._clock += e
        self.sigma -= e
        self.in_celldevs.read_new_events()

        new_state = self.local_computation(deepcopy(self.cell_state))
        if new_state != self.cell_state:
            state = deepcopy(new_state)
            self.out_celldevs.add_to_buffer(self._clock + self.output_delay(state), state)
            self.sigma = self.out_celldevs.next_time() - self._clock
        self.cell_state = new_state

    def lambdaf(self):
        self.out_celldevs.send_events(self._clock + self.sigma)

    def initialize(self):
        self.out_celldevs.add_to_buffer(0, self.cell_state)
        self.activate()

    def exit(self):
        pass

    def _load_neighborhood(self) -> dict[C, V]:
        return self._config.load_neighborhood()
