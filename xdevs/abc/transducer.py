import inspect
import itertools
import logging
import re
from abc import ABC, abstractmethod
from math import isinf, isnan
from typing import Any, Callable, Type, Iterable
from xdevs import T
from xdevs.models import Atomic, Component, Coupled, Port


class Transducible(ABC):
    @classmethod
    @abstractmethod
    def transducer_map(cls) -> dict[str, tuple[Type[T], Callable[[Any], T]]]:
        pass


class Transducer(ABC):

    state_mapper: dict[str, tuple[Type[T], Callable[[Atomic], T]]]
    event_mapper: dict[str, tuple[Type[T], Callable[[Any], T]]]

    def __init__(self, *args, **kwargs):
        """
        Transducer for the xDEVS M&S tool.
        :param str transducer_id: ID of the transducer. This parameter is mandatory.
        :param str sim_time_id: ID of the data field containing the simulation time. By default, it is "sim_time".
        :param bool include_names: when True, the logs include DEVS port and component names. By default, it is True.
        :param str model_name_id: ID of the data field containing the DEVS model name. By default, it is "model_name".
        :param str port_name_id: ID of the data field containing the DEVS port name. By default, it is "port_name".
        :param bool exhaustive: determines if the output contains the state of the target components for each iteration
        (True) or only includes the change states (False).
        """
        self.transducer_id: str = kwargs['transducer_id']
        self.sim_time_id: str = kwargs.get('sim_time_id', 'sim_time')
        self.include_names: bool = kwargs.get('include_names', True)
        self.model_name_id: str = kwargs.get('model_name_id', 'model_name')
        self.port_name_id: str = kwargs.get('port_name_id', 'port_name')
        self.exhaustive: bool = kwargs.get('exhaustive', False)

        self.active: bool = True
        self.target_components: set[Atomic] = set()
        self.target_ports: set[Port] = set()
        self.imminent_components: list[Atomic] | None = None if self.exhaustive else []
        self.imminent_ports: list[Port] | None = None if self.exhaustive else []

        self.state_mapper = {'phase': (str, lambda x: x.phase), 'sigma': (float, lambda x: x.sigma)}
        event_type: Type[T] | None = kwargs.get('event_type')
        if event_type is not None and issubclass(event_type, Transducible):
            self.event_mapper = event_type.transducer_map()
        else:
            self.event_mapper = {'value': (str, lambda x: str(x))}

        self.supported_data_types: Iterable[type] = self.create_known_data_types_map()
        self._remove_special_numbers: bool = False

    def activate_remove_special_numbers(self):
        logging.warning(f'Transducer {self.transducer_id} does not support special number values (e.g., infinity). '
                        'It will automatically substitute these values with None')
        self._remove_special_numbers = True

    def add_target_component(self, component: Component, *filters):
        components = self._iterate_components(component)
        self.target_components |= self._apply_filters(filters, components)

    def _iterate_components(self, root_comp: Component, include_coupled: bool = False):
        if isinstance(root_comp, Atomic):
            yield root_comp
        elif isinstance(root_comp, Coupled):  # Coupled
            if include_coupled:
                yield root_comp
            for child_comp in root_comp.components:
                yield from self._iterate_components(child_comp, include_coupled=include_coupled)
        else:
            raise ValueError(f'Component {root_comp.name} is not an Atomic nor a Coupled')

    def add_target_port(self, port: Port):
        parent: Component | None = port.parent
        if parent is None:
            raise ValueError(f'Port {port.name} does not have a parent component')
        self.target_ports.add(port)

    def add_target_ports_by_component(self, component: Component, component_filters=None, port_filters=None):
        components = self._iterate_components(component, include_coupled=True)
        filtered_components = Transducer._apply_filters(component_filters, components)
        for comp in filtered_components:
            comp_ports = itertools.chain(comp.in_ports, comp.out_ports)
            filtered_comp_ports = Transducer._apply_filters(port_filters, comp_ports)
            self.target_ports |= filtered_comp_ports

    def add_imminent_model(self, component: Atomic):
        if not self.exhaustive and self.active:
            self.imminent_components.append(component)

    def add_imminent_port(self, port: Port):
        if not self.exhaustive and self.active:
            self.imminent_ports.append(port)

    def filter_components(self, *filters):
        self.target_components = self._apply_filters(filters, self.target_components)

    def add_event_field(self, field_name: str, field_type: Type[T], field_getter: Callable[[Any], T]):
        """
        Adds new event field to the event mapper.
        :param field_name: name of the new field.
        :param field_type: data type of the new field.
        :param field_getter: function that takes an event as input and returns the value of the new event field.
        :raise KeyError: if field name is already in event mapper.
        """
        if field_name == self.sim_time_id:
            raise KeyError(f'Field name {field_name} is reserved for the simulation time field')
        elif self.include_names and field_name in (self.model_name_id, self.port_name_id):
            raise KeyError(f'Field name {field_name} is reserved for DEVS element name field')
        self._add_field(self.event_mapper, field_name, field_type, field_getter)

    def add_state_field(self, field_name: str, field_type: Type[T], field_getter: Callable[[Atomic], T]):
        """
        Adds new state field to the state mapper.
        :param field_name: name of the new field.
        :param field_type: data type of the new field.
        :param field_getter: function that takes an atomic model as input and returns the value of the new event field.
        :raise KeyError: if field name is already in state mapper.
        """
        if field_name == self.sim_time_id:
            raise KeyError(f'Field name {field_name} is reserved for the simulation time field')
        elif self.include_names and field_name == self.model_name_id:
            raise KeyError(f'Field name {field_name} is reserved for DEVS component name field')
        self._add_field(self.state_mapper, field_name, field_type, field_getter)

    @staticmethod
    def _add_field(field_mapper: dict[str, tuple[Type[T], Callable[[Any], T]]],
                   field_name: str, field_type: Type[T], field_getter: Callable[[Any], T]):
        if field_name in field_mapper:
            raise KeyError(f'Field name {field_name} is already included in field mapper')
        field_mapper[field_name] = (field_type, field_getter)

    def drop_event_field(self, field_name: str):
        """
        Drops a field from the event mapper.
        :param field_name: name of the field to be removed.
        :raise KeyError: if field name is not in state mapper.
        """
        self.event_mapper.pop(field_name)

    def drop_state_field(self, field_name: str):
        """
        Drops a field from the state mapper.
        :param field_name: name of the field to be removed.
        :raise KeyError: if field name is not in state mapper.
        """
        self.state_mapper.pop(field_name)

    @staticmethod
    def _apply_filters(filters, entities):
        """
        Filter target components or ports.
        :param filters: it can be a callable (lambda model: condition(model)) a
        regex (to filter based on the components name), or a type (to keep instances of a specific name)
        :param entities: components or ports to filter
        """
        filtered_entities = set(entities)
        if filters is not None:
            if type(filters) not in (tuple, list):
                filters = (filters,)
            for entity_filter in filters:
                if inspect.isfunction(entity_filter):
                    filtered_entities = set(filter(entity_filter, filtered_entities))
                elif type(entity_filter) is str:
                    filtered_entities = set(filter(lambda c: re.match(entity_filter, c.name), filtered_entities))
                else:
                    filtered_entities = set(filter(lambda c: isinstance(c, entity_filter), filtered_entities))

        return filtered_entities

    def pause(self):
        self.active = False

    def resume(self):
        self.active = True

    @abstractmethod
    def create_known_data_types_map(self) -> Iterable[type]:
        """
        Returns an iterable (e.g., a list, a dictionary, etc.) of data types that are known by the transducer.
        Unknown data types will be automatically transformed to string.
        :return: Iterable of known/supported data types.
        """
        pass

    @abstractmethod
    def initialize(self):
        """Executes any required action before starting simulation (e.g., creating output file)."""
        pass

    @abstractmethod
    def exit(self):
        """Executes any required action after complete simulation (e.g., close output file)."""
        pass

    @abstractmethod
    def bulk_data(self, sim_time: float):
        """Executes any required action for bulking new data to the destination."""
        pass

    def trigger(self, sim_time: float):
        if self.active:
            self.bulk_data(sim_time)
            if not self.exhaustive:
                self.imminent_components.clear()
                self.imminent_ports.clear()

    def _iterate_state_inserts(self, sim_time: float):
        components = self.target_components if self.exhaustive else self.imminent_components
        # TODO: filter actually changed states
        for component in components:
            fields = {self.sim_time_id: sim_time}
            if self.include_names:
                fields.update({self.model_name_id: component.name})
            extra_fields = self.map_extra_fields(component, self.state_mapper)
            yield {**fields, **extra_fields}

    def _iterate_event_inserts(self, sim_time: float):
        ports = self.target_ports if self.exhaustive else self.imminent_ports

        for port in ports:
            for event in port.values:
                fields = {self.sim_time_id: sim_time}
                if self.include_names:
                    fields.update({self.model_name_id: port.parent.name, self.port_name_id: port.name})
                extra_fields = self.map_extra_fields(event, self.event_mapper)
                yield {**fields, **extra_fields}

    def map_extra_fields(self, target: Any, field_mapper: dict) -> dict[str, Any]:
        """
        Maps fields from target object according to a field mapper.
        :param target: target object that contains the additional data.
        :param field_mapper: field mapper. It has the following structure: {'field_id': (data_type, getter_function)}.
        :return: dictionary with the values to be bulked to the destination.
        """
        extra_fields: dict[str, Any] = dict()
        for field_id, (field_type, field_mapper) in field_mapper.items():
            field_value = field_mapper(target)  # subtract extra field from target
            if field_type not in self.supported_data_types:
                field_value = str(field_value)  # unknown data types are automatically converted to string
            elif self._remove_special_numbers and field_type in (int, float):
                if field_value is not None and (isnan(field_value) or isinf(field_value)):
                    field_value = None  # special numeric values are changed to None when required
            extra_fields[field_id] = field_value
        return extra_fields

    def _log_unknown_data(self, data_type: type, field_name: str):
        logging.warning(f'Transducer {self.transducer_id} does not support data type {data_type} of field {field_name}. '
                        'It will cast it to string')
