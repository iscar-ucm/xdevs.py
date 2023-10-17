# This approach is based on the java implementation in xdevs.java

# Now we are dealing with a GPT model instead of an EFP.

import importlib
import logging
import json

from xdevs.models import Coupled, Atomic, Port
from xdevs.examples.basic.basic import Processor, Transducer, Generator


# TODO fabrica componentes
def create_atomic(info: dict):

    name = info.get('name', None)
    clase: str = info.get('class', None)
    valores = info.get('kwargs')
    ato = None
    # print(f'clase = {clase}')
    # print(f'valores = {valores}')

    if clase.split('.')[-1] == 'Processor':
        ato = Processor(name=name, proc_time=valores.get('proc_time'))
    elif clase.split('.')[-1] == 'Transducer':
        ato = Transducer(name=name, obs_time=valores.get('obs_time'))
    elif clase.split('.')[-1] == 'Generator':
        ato = Generator(name=name, period=valores.get('period'))
    else:
        pass

    return ato

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
                print('!!!!!')
                port_to = dict_comp[connection['componentTo']].get_in_port(connection['portTo'])
                p_in = Port(p_type=type(port_to), name=connection['portFrom'])
                padre.add_in_port(p_in)
                padre.add_coupling(padre.get_in_port(p_in.name), port_to)

            # Connexion eoc
            elif connection['componentFrom'] in dict_comp and connection['componentTo'] is None:
                print('¡¡¡¡¡')
                port_from = dict_comp[connection['componentFrom']].get_out_port(connection['portFrom'])
                p_out = Port(p_type=type(port_from), name=connection['portOut'])
                padre.add_out_port(p_out)
                padre.add_coupling(port_from, padre.get_out_port(p_out.name))

            else:
                raise Exception('Ports not found')

    return padre








with open("coupled_model_v2.json") as f:
    file = json.load(f)

Comp = list()
Conections = list()

PJ = Coupled(name='ModelTest')

C = from_json(file)
print(C)

print(f'Componentes añadidos: {Comp}')

print(f'Conexiones añadidos: {Conections}')
