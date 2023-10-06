import distutils.cygwinccompiler
import json
from xdevs.examples.basic.basic import Generator, Processor, Transducer

with open("coupled_model.json") as f:
    file = json.load(f)


Components_json = list()    # lista para guardar los dict de cada componente
Conex = list()  # Lista para guardar todas las conexiones que tienen que hacerse
Comp = list()   # Lista final para guardar los objetos creados
def unwrap_components(**dic: dict):
    for k, v in dic.get("components").items():
        if isinstance(v, dict):
            #print(f'{k} = {v}', flush=True)
            if not v.get("components").items():
                Components_json.append(v)
            unwrap_components(**v)
        elif isinstance(v, list):
            #print(f'Conexiones: {v}', flush=True)
            Conex.append(v)
        else:
            pass


def create_components(comp: list[dict]):
    # Creamos componentes como una tupla (id, objeto) Para luego hacer las conexiones ayudandonos del id que es el que
    # usa en JSON
    for item in comp:
        if item.get("type") == "Processor":
            Comp.append((item.get("id"), Processor(**item.get("att"))))
        elif item.get("type") == "Generator":
            Comp.append((item.get("id"), Generator(**item.get("att"))))
        elif item.get("type") == "Transducer":
            Comp.append((item.get("id"), Transducer(**item.get("att"))))
        else:
            pass




unwrap_components(**file)
create_components(Components_json)

print(len(Comp))
"""
print(Components_json, len(Components_json))

Conex = Conex[::-1] # Es necesario girar la lista de conexiones para ir de fuera a dentro. OJO porque cuando tengamos 
                    # acoplados (distintas ramas hacia abajo) esto se va a romper. 
print(Conex, len(Conex))
"""