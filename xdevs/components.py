import pkg_resources
import  json
from typing import ClassVar
from xdevs.models import Component, Port, Coupled


class Components:
    """
        This class creates components from unique identifiers called "component_id".

        In order to identify each component_id check the "entry_point" dict in the file setup.py and look for the
        list 'xdevs.plugins.components'.
    """
    _plugins: ClassVar[dict[str, type[Component]]] = {
        ep.name: ep.load() for ep in pkg_resources.iter_entry_points('xdevs.plugins.components')
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
            for connection in config.get('connections', []):
                child_from = connection.get('componentFrom')
                child_to = connection.get('componentTo')
                if child_from is not None:
                    child_from = children[child_from]
                    port_from = child_from.get_out_port(connection['portFrom'])
                    if port_from is None:
                        raise Exception(f'Invalid connection in: {connection}. Reason: portFrom not found')
                    if child_to is not None:
                        # this is an IC
                        child_to = children[child_to]
                        port_to = child_to.get_in_port(connection['portTo'])
                        if port_to is None:
                            raise Exception(f'Invalid connection in: {connection}. Reason: portTo not found')
                    else:
                        # this is an EOC
                        port_to = child_to.get_in_port(connection['portTo'])
                        if port_to is None:
                            port_to = Port(p_type=port_from.p_type, name=connection['portTo'])
                            component.add_out_port(port_to)
                elif child_to is not None:
                    # this is an EIC
                    child_to = children[child_to]
                    port_to = child_to.get_in_port(connection['portTo'])
                    if port_to is None:
                        raise Exception(f'Invalid connection in: {connection}. Reason: portTo not found')
                    port_from = component.get_in_port(connection['portFrom'])
                    if port_from is None:
                        port_from = Port(p_type=port_to.p_type, name=connection['portFrom'])
                        component.add_in_port(port_from)
                else:
                    raise Exception(
                        f'Invalid connection in: {connection}. Reason: componentFrom and componentTo are None')

                component.add_coupling(port_from, port_to)
        else:
            raise Exception('No component found')
        return component

    @staticmethod
    def from_json(file_path: str):
        """
        A function to parser a json file into a DEVS model

        Considering the following constrains, the json file structure is as follows:

        When adding a component if it contains the key "component_id", the component will be created using it and the
        kwargs associated with it. The "component_id" value refers to the key to identify each component in the class
        Components.

        When the component does not have the key "component_id" it must have the pair keys "components" and "connections".
        This component will be implementing several components and their connections inside itself.

        The connections are created using four keys:
            - If both componentFrom/To keys are added, the connection will be of the type IC.
            - If componentFrom key is missing, the connection will be of the type EIC.
            - If componentTo key is missing, the connection will be of the type EOC.
            - If any portFrom/To value is missing the connections is not established.

        Structure:

        - 'MasterComponentName' (dict): The master component.
        - 'components' (dict): A dictionary containing multiple components.
            - 'ComponentName1' (dict): Iterative component.
                - 'components' (dict): Nested components if any.
                - 'connections' (list): List of connection dictionaries.
                    - 'componentFrom' (str): Name of the component where the connection starts.
                    - 'portFrom' (str): Port name from 'componentFrom'.
                    - 'componentTo' (str): Name of the component where the connection ends.
                    - 'portTo' (str): Port name from 'componentTo'.
            - 'ComponentName2' (dict): Single component.
                - 'component_id' (str): ID read from the factory for this component.
                - 'kwargs' (dict): Keyword arguments for the component.
                    - 'a_parameter' (any): A parameter for the component.
                    - ... : Other keyword arguments if any.
            - ... : Additional components if any.
        - 'connections' (list): List of connection dictionaries at the top level.
            - 'componentFrom' (str): Name of the component where the connection starts.
            - 'portFrom' (str): Port name from 'componentFrom'.
            - 'componentTo' (str): Name of the component where the connection ends.
            - 'portTo' (str): Port name from 'componentTo'.

        :param file_path: Path to the JSON file
        :return: a Coupled DEVS model
        """

        with open(file_path) as f:
            data = json.load(f)

        name = list(data.keys())[0]  # Gets the actual component name
        config = data[name]  # Gets the actual component config

        return Components._nested_component(name, config)


if __name__ == '__main__':

    C = Components.from_json('coupled_model_v2.json')
    print(C)
