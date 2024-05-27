from __future__ import annotations
import json
from importlib.metadata import entry_points
from typing import ClassVar
from xdevs.abc import InputHandler, OutputHandler, Transducer
from xdevs.models import Atomic, Component, Port, Coupled


class InputHandlers:
    _plugins: ClassVar[dict[str, type[InputHandler]]] = {
        ep.name: ep.load() for ep in entry_points(group='xdevs.input_handlers')
    }

    @staticmethod
    def add_plugin(name: str, plugin: type[InputHandler]):
        """
        Registers a custom input handler to the plugin system.

        :param name: name used to identify the custom input handler. It must be unique.
        :param plugin: custom input handler type. Note that it must not be an object, just the class.
        """
        if name in InputHandlers._plugins:
            raise ValueError(f'xDEVS input_handler plugin with name "{name}" already exists')
        InputHandlers._plugins[name] = plugin

    @staticmethod
    def create_input_handler(name: str, *args, **kwargs) -> InputHandler:
        """
        Creates a new input handler. Note that this is done by the real-time manager.
        Users do not directly create input handlers using this method.

        :param name: unique ID of the input handler to be created.
        :param kwargs: any additional configuration parameter needed for creating the input handler.
        :return: an instance of the InputHandler class.
        """
        if name not in InputHandlers._plugins:
            raise ValueError(f'xDEVS input_handler plugin with name "{name}" not found')
        return InputHandlers._plugins[name](*args, **kwargs)


class OutputHandlers:
    _plugins: ClassVar[dict[str, type[OutputHandler]]] = {
        ep.name: ep.load() for ep in entry_points(group='xdevs.output_handlers')
    }

    @staticmethod
    def add_plugin(name: str, plugin: type[OutputHandler]):
        """
        Registers a custom output handler to the plugin system.

        :param name: name used to identify the custom input handler. It must be unique.
        :param plugin: custom input handler type. Note that it must not be an object, just the class.
        """
        if name in OutputHandlers._plugins:
            raise ValueError(f'xDEVS output_handler plugin with name "{name}" already exists')
        OutputHandlers._plugins[name] = plugin

    @staticmethod
    def create_output_handler(name: str, *args, **kwargs) -> OutputHandler:
        """

        Creates a new output handler. Note that this is done by the real-time manager.
        Users do not directly create output handlers using this method.

        :param name: unique ID of the output handler to be created.
        :param kwargs: any additional configuration parameter needed for creating the output handler.
        :return: an instance of the OutputHandler class.
        """
        if name not in OutputHandlers._plugins:
            raise ValueError(f'xDEVS output_handler plugin with name "{name}" not found')
        return OutputHandlers._plugins[name](*args, **kwargs)


class Wrappers:
    _plugins: ClassVar[dict[str, type[Atomic]]] = {
        ep.name: ep.load() for ep in entry_points(group='xdevs.wrappers')
    }

    @staticmethod
    def add_plugin(name: str, plugin: type[Atomic]):
        if name in Wrappers._plugins:
            raise ValueError(f'xDEVS wrapper plugin with name "{name}" already exists')
        Wrappers._plugins[name] = plugin

    @staticmethod
    def create_wrapper(name: str, *args, **kwargs) -> Atomic:
        if name not in Wrappers._plugins:
            raise ValueError(f'xDEVS wrapper plugin with name "{name}" not found')
        return Wrappers._plugins[name](*args, **kwargs)


class Transducers:
    _plugins: ClassVar[dict[str, type[Transducer]]] = {
        ep.name: ep.load() for ep in entry_points(group='xdevs.transducers')
    }

    @staticmethod
    def add_plugin(name: str, plugin: type[Transducer]):
        if name in Transducers._plugins:
            raise ValueError(f'xDEVS transducer plugin with name "{name}" already exists')
        Transducers._plugins[name] = plugin

    @staticmethod
    def create_transducer(name: str, *args, **kwargs) -> Transducer:
        if name not in Transducers._plugins:
            raise ValueError(f'xDEVS transducer plugin with name "{name}" not found')
        return Transducers._plugins[name](*args, **kwargs)


class Components:
    """This class creates components from unique identifiers called "component_id"."""
    _plugins: ClassVar[dict[str, type[Component]]] = {
        ep.name: ep.load() for ep in entry_points(group='xdevs.components')
    }

    @staticmethod
    def add_plugin(component_id: str, plugin: type[Component]):
        if component_id in Components._plugins:
            raise ValueError(f'xDEVS component plugin with name "{component_id}" already exists')
        Components._plugins[component_id] = plugin

    @staticmethod
    def create_component(component_id: str, *args, **kwargs) -> Component:
        if component_id not in Components._plugins:
            raise ValueError(f'xDEVS component plugin with name "{component_id}" not found')
        return Components._plugins[component_id](*args, **kwargs)

    @staticmethod
    def _nested_component(name: str, config: dict) -> Component:
        if 'component_id' in config:
            # Predefined component, use factory
            component_id: str = config['component_id']
            args = config.get('args', [])
            kwargs = config.get('kwargs', {})
            kwargs['name'] = name
            return Components.create_component(component_id, *args, **kwargs)
        elif 'components' in config:
            # It is a coupled model
            component = Coupled(name)
            children: dict[str, Component] = dict()
            # Create children components
            for component_name, component_config in config['components'].items():
                child = Components._nested_component(component_name, component_config)
                children[component_name] = child
                component.add_component(child)
            # Create connections
            for coupling in config.get('couplings', []):
                child_from = coupling.get('componentFrom')
                child_to = coupling.get('componentTo')
                if child_from is not None:
                    child_from = children[child_from]
                    port_from = child_from.get_out_port(coupling['portFrom'])
                    if port_from is None:
                        raise Exception(f'Invalid coupling in: {coupling}. Reason: portFrom not found')
                    if child_to is not None:
                        # this is an IC
                        child_to = children[child_to]
                        port_to = child_to.get_in_port(coupling['portTo'])
                        if port_to is None:
                            raise Exception(f'Invalid coupling in: {coupling}. Reason: portTo not found')
                    else:
                        # this is an EOC
                        port_to = child_to.get_in_port(coupling['portTo'])
                        if port_to is None:
                            port_to = Port(p_type=port_from.p_type, name=coupling['portTo'])
                            component.add_out_port(port_to)
                elif child_to is not None:
                    # this is an EIC
                    child_to = children[child_to]
                    port_to = child_to.get_in_port(coupling['portTo'])
                    if port_to is None:
                        raise Exception(f'Invalid coupling in: {coupling}. Reason: portTo not found')
                    port_from = component.get_in_port(coupling['portFrom'])
                    if port_from is None:
                        port_from = Port(p_type=port_to.p_type, name=coupling['portFrom'])
                        component.add_in_port(port_from)
                else:
                    raise Exception(
                        f'Invalid coupling in: {coupling}. Reason: componentFrom and componentTo are None')

                component.add_coupling(port_from, port_to)
        else:
            raise Exception('No component found')
        return component

    @staticmethod
    def from_json(file_path: str):
        """
        A function to parser a JSON file into a DEVS model. The JSON file structure should follow the next rules:

        When adding a component, if it contains the key "component_id", the component will be created using it and the
        args and kwargs associated with it. The "component_id" value refers to the key to identify each component in
        the class Components.

        When the component does not have the key "component_id", it is assumed to be a coupled model.
        Therefore, it must have the keys "components" and "couplings".
        This component will be implementing several components and their couplings inside itself.

        The couplings are created using four keys:
            - If both componentFrom/To keys are added, the connection will be of the type IC.
            - If componentFrom key is missing, the connection will be of the type EIC.
            - If componentTo key is missing, the connection will be of the type EOC.
            - If any portFrom/To value is missing the connections is not valid.

        Structure:

        - 'MasterComponentName' (dict): The master component.
        - 'components' (dict): A dictionary containing multiple components.
            - 'ComponentName1' (dict): Iterative component.
                - 'components' (dict): Nested components if any.
                - 'couplings' (list): List of connection dictionaries.
                    - 'componentFrom' (str): Name of the component where the connection starts.
                    - 'portFrom' (str): Port name from 'componentFrom'.
                    - 'componentTo' (str): Name of the component where the connection ends.
                    - 'portTo' (str): Port name from 'componentTo'.
            - 'ComponentName2' (dict): Single component.
                - 'component_id' (str): ID read from the factory for this component.
                - 'args' (list): Positional arguments for the component.
                - 'kwargs' (dict): Keyword arguments for the component.
                    - 'a_parameter' (any): A parameter for the component.
                    - ... : Other keyword arguments if any.
            - ... : Additional components if any.
        - 'couplings' (list): List of couplings.
            - 'componentFrom' (str): Name of the component where the connection starts.
            - 'portFrom' (str): Port name from 'componentFrom'.
            - 'componentTo' (str): Name of the component where the connection ends.
            - 'portTo' (str): Port name from 'componentTo'.

        :param file_path: Path to the JSON file
        :return: a DEVS model according to the JSON file
        """
        with open(file_path) as f:
            data = json.load(f)

        name = list(data.keys())[0]  # Gets the actual component name
        config = data[name]  # Gets the actual component config

        return Components._nested_component(name, config)
