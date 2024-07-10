from __future__ import annotations
import queue
import threading

try:
    from paho.mqtt.client import Client
    from xdevs.abc.handler import InputHandler



    def on_connect(client, userdata, flags, rc):
        print(f'MQTT client connected with mqtt: {rc}')  # rc value for success or failure
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

    def mqtt_parser(mqtt_msg):
        topic = [item for item in mqtt_msg.topic.split('/')]
        port = topic[-1]

        msg = mqtt_msg.payload.decode()
        return port, msg

    class MQTTInputHandler(InputHandler):
        def __init__(self, subscriptions: dict[str, int] = None, **kwargs):
            """
            This input handler is the implementation of the MQTT protocol.
            It subscribes to the desired topics and pushes the messages received to the system

            :param dict[str, int] subscriptions: dict of topics and their QoS. Default is None
            :param str host: desired MQTT broker. Default is 'test.mosquitto.org'
            :param int port: port of the MQTT broker to be used. Default is 1883
            :param int keepalive: keepalive time for the MQTT connection. Default is 60
            :param Callable[[mqtt.Message], str, str] event_parser: from the received message obtain the topic and the message payload. Default is mqtt_parser
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


except ImportError:
    from .bad_dependencies import BadDependenciesHandler


    class MQTTInputHandler(BadDependenciesHandler):
        def __init__(self, **kwargs):
            super().__init__(handler_type='mqtt', **kwargs)
