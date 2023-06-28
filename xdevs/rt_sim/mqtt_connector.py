class Connector():
    def __init__(self, conections: dict[str, str]):

        """
        Función para conectar de forma correcta los puertos (que usen protocolo MQTT)

        :param conections: dict[key: str, value: str]. Donde la key es el puerto de al que me quiero conectar y el
            value es el puerto de mi acoplado.
        """

        self.connections: dict[str, str] = conections

    def input_handler(self, port: str):
        #print(f'Le paso port = {port}')
        #print(self.connections)
        if self.connections is not None:
            for key, value in self.connections.items():
                if port == key:
                    return value
            #print(f'Devuelvo port = {port}')
        return port


