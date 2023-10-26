# This approach is based on the java implementation in xdevs.java

# Now we are dealing with a GPT model instead of an EFP.

import importlib
import logging
import json
import pkg_resources
from typing import ClassVar, Type

from xdevs.models import Coupled, Atomic, Port
from xdevs.examples.basic.basic import Processor, Transducer, Generator
from xdevs.models import Component
from xdevs.sim import Coordinator


def create_atomic(info: dict):
    name = info.get('name', None)
    clase: str = info.get('class', None)
    valores = info.get('kwargs')

    component = ComponentsFactory.create_component_handler(class_id=clase, name=name, **valores)
    return component


# @staticmethod de la clase Coupled
def from_json(data):
    name = list(data.keys())[0]  # Obtiene el nombre del componente acoplado actual
    print(name)
    padre = Coupled(name)
    dict_comp = dict()  # dict para almacenar los componentes

    for key in data[name].get('components', {}):
        current_data = data[name]['components'][key]

        if 'components' in current_data:

            hijo = from_json({key: current_data})
            padre.add_component(hijo)
            dict_comp[hijo.name] = hijo

        elif 'name' in current_data:
            at = create_atomic(current_data)
            Comp.append(at)
            dict_comp[at.name] = at
            padre.add_component(at)

        else:
            raise Exception('No component found')

    if 'connections' in data[name]:
        connections_data = data[name]['connections']
        # print(dict_comp)
        for connection in connections_data:
            # print(connection)

            # Connexion ic
            if connection['componentFrom'] in dict_comp and connection['componentTo'] in dict_comp:
                port_from = dict_comp[connection['componentFrom']].get_out_port(connection['portFrom'])
                port_to = dict_comp[connection['componentTo']].get_in_port(connection['portTo'])
                padre.add_coupling(port_from, port_to)

            # Connexion eic
            elif connection['componentFrom'] is None and connection['componentTo'] in dict_comp:
                # print('!!!!!')
                port_to = dict_comp[connection['componentTo']].get_in_port(connection['portTo'])
                p_in = Port(p_type=port_to.p_type, name=connection['portFrom'])
                padre.add_in_port(p_in)
                padre.add_coupling(padre.get_in_port(p_in.name), port_to)

            # Connexion eoc
            elif connection['componentFrom'] in dict_comp and connection['componentTo'] is None:
                # print('¡¡¡¡¡')
                port_from = dict_comp[connection['componentFrom']].get_out_port(connection['portFrom'])
                p_out = Port(p_type=port_from.p_type, name=connection['portOut'])
                padre.add_out_port(p_out)
                padre.add_coupling(port_from, padre.get_out_port(p_out.name))

            else:
                raise Exception('Ports not found')

    return padre


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


with open("coupled_model_v2.json") as f:
    file = json.load(f)

Comp = list()
Conections = list()

PJ = Coupled(name='ModelTest')

C = from_json(file)

#   G = ComponentsFactory.create_component_handler('Generator', name='GenTest', period=3)
#   P = ComponentsFactory.create_component_handler('Processor', name='PTest', proc_time=5)

#   print(C, P, G)

print(f'Componentes añadidos: {Comp}')
for c in Comp:
    print(c)

print(f'Conexiones añadidos: {Conections}')
