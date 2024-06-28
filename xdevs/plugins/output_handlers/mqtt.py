from __future__ import annotations
from typing import Callable, Any

try:
    from xdevs.abc.handler import OutputHandler
    from ..input_handlers.mqtt import MQTTClient


    class MQTTOutputHandler(OutputHandler):
        """
        This output handler is the implementation of the MQTT protocol.
        It publishes events to the desired topics.

        :param str host: desired MQTT broker. Default is 'test.mosquitto.org'
        :param int port: port of the MQTT broker to be used. Default is 1883
        :param int keepalive: keepalive time for the MQTT connection. Default is 60
        :param str topic: desired topic to publish the events. Default is 'RTsys' and generate the topic as 'RTsys/output/<port>'
        :param Callable[[str, str], Tuple[str,str]] event_parser: function to parser the port and the message to be
                ejected into a MQTT topic and the payload of the MQTT message.
        """
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

            self.host = kwargs.get('host', 'test.mosquitto.org')
            self.port = kwargs.get('port', 1883)
            self.keepalive = kwargs.get('keepalive', 60)

            self.client = MQTTClient()

            self.topic: str = kwargs.get('topic', 'RTsys')

            self.event_parser: Callable[[str, Any], str] = kwargs.get('event_parser',
                                                                lambda port, msg: (f'{self.topic}/output/{port}', msg))

        def initialize(self):
            self.client.connect(self.host, self.port, self.keepalive)

        def run(self):
            while True:
                topic, payload = self.pop_event()
                print(f'Publishing {payload} to {topic}')
                self.client.publish(topic, payload)


except ImportError:
    from .bad_dependencies import BadDependenciesHandler


    class MQTTOutputHandler(BadDependenciesHandler):
        def __init__(self, **kwargs):
            super().__init__(handler_type='mqtt', **kwargs)
