# This approach is based on the java implementation in xdevs.java
import json
import sys
from xdevs.models import Coupled, Port, Component
from xdevs.sim import Coordinator
from xdevs.components import Components


def nested_component(name: str, config: dict) -> Component:
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
            child = nested_component(component_name, component_config)
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
                child_to = children[child_to]
                port_to = child_to.get_in_port(connection['portTo'])
                if port_to is None:
                    raise Exception(f'Invalid connection in: {connection}. Reason: portTo not found')
                port_from = component.get_in_port(connection['portFrom'])
                if port_from is None:
                    port_from = Port(p_type=port_to.p_type, name=connection['portFrom'])
                    component.add_in_port(port_from)
            else:
                raise Exception(f'Invalid connection in: {connection}. Reason: componentFrom and componentTo are None')

            component.add_coupling(port_from, port_to)
    else:
        raise Exception('No component found')
    return component


# @staticmethod de la clase Coupled
def from_json(file):
    """
    A function to parser a json file into a DEVS model
    
    The structure of the json file must be as follows:

    {
    "MasterCoupledName": {
        "components" : {

            "ThisIsACoupledModel" :{
                "components" : {}
                "connections" : []
            },

            "ThisIsAAtomicModel" : {
                "name": "AtomicName",
                "class": "AtomicClassIdentifier",
                "kwargs": {
                    "a_parameter" : ,
                    ...
                }
            },

            ...

        },
        "connections": [
            {
                "componentFrom": "",
                "portFrom": "",
                "componentTo": "",
                "portTo": ""
            },

            ...
            
            ]
        }
    }

    :param file: Path to the JSON file
    :return: a Coupled DEVS model
    """

    with open("coupled_model.json") as f:
        data = json.load(f)
    
    name = list(data.keys())[0]  # Gets the actual component name
    config = data[name]  # Gets the actual component config
    
    return nested_component(name, config)


if __name__ == '__main__':
    file = "coupled_model.json"

    print(type(file))
    Comp = list()
    Connections = list()

    C = from_json(file)

    print(f'Componentes añadidos: {Comp}')
    for c in Comp:
        print(c)

    Coord = Coordinator(C)
    Coord.initialize()
    Coord.simulate()
