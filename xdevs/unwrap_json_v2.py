# This approach is based on the java implementation in xdevs.java
import json
import sys

import pkg_resources
from typing import ClassVar, Type

from xdevs.models import Coupled, Atomic, Port
from xdevs.examples.basic.basic import Processor, Transducer, Generator
from xdevs.models import Component
from xdevs.sim import Coordinator


def create_component(info: dict):
    """
    A function to create components based on the ComponentsFactory

    :param info: a dictionary that contains the class_id and the arguments to create the component
    :return: a component (Coupled/Atomic) with the parameters set in info
    """
    name = info.get('name', None)
    class_id: str = info.get('class', None)
    values = info.get('kwargs')
    component = ComponentsFactory.create_component_handler(class_id=class_id, name=name, **values)
    return component


# @staticmethod de la clase Coupled
def from_json(data):
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

    :param data: a loaded json file of the type dict
    :return: a Coupled DEVS model
    """
    
    name = list(data.keys())[0]  # Gets the actual component name
    print(name)
    parent = Coupled(name)
    dict_comp = dict()  # dict to storage the components

    for key in data[name].get('components', {}):
        current_data = data[name]['components'][key]

        if 'components' in current_data:

            child = from_json({key: current_data})
            parent.add_component(child)
            dict_comp[child.name] = child

        elif 'name' in current_data:
            component = create_component(current_data)
            Comp.append(component)
            dict_comp[component.name] = component
            parent.add_component(component)

        else:
            raise Exception('No component found')

    if 'connections' in data[name]:
        connections_data = data[name]['connections']
        # print(dict_comp)
        for connection in connections_data:
            # print(connection)
            try:
                # Connexion ic
                if connection['componentFrom'] in dict_comp and connection['componentTo'] in dict_comp:
                    port_from = dict_comp[connection['componentFrom']].get_out_port(connection['portFrom'])
                    port_to = dict_comp[connection['componentTo']].get_in_port(connection['portTo'])
                    parent.add_coupling(port_from, port_to)

                # Connexion eic
                elif connection['componentFrom'] is None and connection['componentTo'] in dict_comp:
                    # print('!!!!!')
                    port_to = dict_comp[connection['componentTo']].get_in_port(connection['portTo'])
                    p_in = Port(p_type=port_to.p_type, name=connection['portFrom'])
                    parent.add_in_port(p_in)
                    parent.add_coupling(parent.get_in_port(p_in.name), port_to)

                # Connexion eoc
                elif connection['componentFrom'] in dict_comp and connection['componentTo'] is None:
                    # print('¡¡¡¡¡')
                    port_from = dict_comp[connection['componentFrom']].get_out_port(connection['portFrom'])
                    p_out = Port(p_type=port_from.p_type, name=connection['portOut'])
                    parent.add_out_port(p_out)
                    parent.add_coupling(port_from, parent.get_out_port(p_out.name))

                else:
                    raise Exception(f'Connection Error! -> {connection}')

            except Exception as e:
                print(f'Invalid connection in: {connection}. Reason: {e}', file=sys.stderr)
                raise

    return parent


class ComponentsFactory:
    _plugins: ClassVar[dict[str, Type[Component]]] = {
        ep.name: ep.load() for ep in pkg_resources.iter_entry_points('xdevs')}

    @staticmethod
    def add_plugin(name: str, plugin: Type[Component]):
        """
        Registers a custom component to the plugin system.

        :param name: name used to identify the custom component. It must be unique.
        :param plugin: custom component type. Note that it must not be an object, just the class.
        """
        if name in ComponentsFactory._plugins:
            raise ValueError('xDEVS component plugin with name "{}" already exists'.format(name))
        ComponentsFactory._plugins[name] = plugin

    @staticmethod
    def create_component_handler(class_id: str, **kwargs) -> Component:
        """
        Creates a new component.

        :param class_id: unique ID of the component to be created.
        :param kwargs: any additional configuration parameter needed for creating the component.
        :return: an instance of the Component class.
        """
        if class_id not in ComponentsFactory._plugins:
            raise ValueError('xDEVS component plugin with name "{}" not found'.format(class_id))
        return ComponentsFactory._plugins[class_id](**kwargs)


if __name__ == '__main__':
    with open("coupled_model.json") as f:
        file = json.load(f)

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
