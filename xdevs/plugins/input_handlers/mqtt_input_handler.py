import datetime
import queue
import threading

from paho.mqtt.client import Client
from xdevs.rt_sim.input_handler import InputHandler



# Desde este input handler me subscribo a topics para ver los mensajes que entran
# ruta: RTsys/coupled_name/input/port_name y to_do lo que llegue a ese puerto se inyecta.


#########################################################################
#########################################################################
#########################################################################
def on_connect(client, userdata, flags, rc):
    print(f'MQTT client connected with mqtt: {rc}')  # rc valor de exito o fracaso en la conexion
    return rc

def on_message(client, userdata, msg):
    # print(f'New msg arrived in {msg.topic} : {msg.payload.decode()} ')
    client.event_queue.put(msg)


class MQTTClient(Client):
    def __init__(self, event_queue: queue = None, **kwargs):
        super().__init__(**kwargs)

        self.on_message = kwargs.get('on_message', on_message)
        self.on_connect = kwargs.get('on_connect', on_connect)

        self.event_queue = event_queue


#########################################################################
#########################################################################
#########################################################################

def mqtt_parser(mqtt_msg):
    topic = [item for item in mqtt_msg.topic.split('/')]
    port = topic[-1]

    msg = mqtt_msg.payload.decode()
    return port, msg

class MQTTInputHandler(InputHandler):
    def __init__(self, subscriptions: dict[str, int] = None, **kwargs):
        """

        :param subscriptions: diccionario con los topics y su qos
        :param kwargs:
        """

        kwargs['event_parser'] = kwargs.get('event_parser', mqtt_parser)

        super().__init__(**kwargs)

        self.subscriptions = subscriptions
        self.host: str = kwargs.get('host', 'test.mosquitto.org')
        self.port: int = kwargs.get('port', 1883)
        self.keepalive: int = kwargs.get('keepalive', 60)

        self.event_queue: queue.SimpleQueue = queue.SimpleQueue()
        self.client = MQTTClient(event_queue=self.event_queue)

        self.client_thread: threading.Thread = threading.Thread(target=self.client.loop_forever, daemon=True)

    def initialize(self):
        self.client.connect(self.host, self.port, self.keepalive)
        for topic, qos in self.subscriptions.items():
            self.client.subscribe(topic, qos)

        self.client_thread.start()

    def run(self):
        while True:
            event = self.event_queue.get()
            print(f'MQTT: Event pushed')    # {event} t = {datetime.datetime.now()}')
            self.push_event(event)

if __name__ == '__main__':
    input_queue = queue.SimpleQueue()
    event_Q = queue.SimpleQueue()

    sub: dict = {
        'ALSW/#': 0,
        'ALSW/TEP': 0,
        'RTsys/#': 0,
    }
    # C = MQTTClient(event_queue=event_Q)
    IN = MQTTInputHandler(queue=input_queue, subscriptions=sub)
    IN.initialize()
    IN.run()
