from typing import Callable, Any

try:
    from xdevs.abc.handler import OutputHandler
    from ..input_handlers import MQTTClient


    class MQTTOutputHandler(OutputHandler):
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
                self.client.publish(topic, payload)


except ImportError:
    from .bad_dependencies import BadDependenciesHandler


    class MQTTOutputHandler(BadDependenciesHandler):
        def __init__(self, **kwargs):
            super().__init__(handler_type='mqtt', **kwargs)
