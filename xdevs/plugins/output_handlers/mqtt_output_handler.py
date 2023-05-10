import threading
import  time
from typing import Callable, Any

from xdevs.plugins.input_handlers.mqtt_input_handler import MQTTClient
from xdevs.rt_sim.output_handler import OutputHandler


class MQTTOutputHandler(OutputHandler):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.host = kwargs.get('host', 'test.mosquitto.org')
        self.port = kwargs.get('port', 1883)
        self.keepalive = kwargs.get('keepalive', 60)

        self.client = MQTTClient()

        self.topic: str = kwargs.get('topic', 'RTsys')

        self.event_parser: Callable[[str, Any], str] = kwargs.get('event_parser',
                                                            lambda port, msg: (f'{self.topic}/Output/{port}', msg))

    def initialize(self):
        self.client.connect(self.host, self.port, self.keepalive)
        print('MQTT connected')

    def run(self):
        print('MQTT running...')
        while True:
            topic, payload = self.pop_event()
            self.client.publish(topic, payload)
            print(f'MQTT sends : {topic} : {payload}')


if __name__ == '__main__':
    def inject_msg():
        print(f'Thread active')
        for i in range(20):
            OUT.queue.put(('Port', f' msg: {i} '))
            print(f'Msg in q and i = {i}')
            if i == 3:
                time.sleep(15)
            else:
                time.sleep(2.5)
        print('Closing...')


    OUT = MQTTOutputHandler()
    OUT.initialize()
    t = threading.Thread(target=inject_msg, daemon=True)
    t.start()
    OUT.run()
