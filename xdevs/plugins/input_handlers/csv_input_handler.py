import csv
import time
from typing import Callable, Any
from xdevs.rt_sim.input_handler import InputHandler


class CSVInputHandler(InputHandler):
    def __init__(self, **kwargs):
        """
        TODO documentation

        :param str file: CSV file path.
        :param str delimiter: column delimiter in CSV file. By default, it is set to ','.
        :param dict[str, Callable[[str], Any]] parsers: message parsers. Keys are port names, and values are functions
        that take an string and returns an object of the corresponding port type. If a parser is not defined, this
        input handler assumes that the port type is str and forward the message as is. By default, all the ports
        are assumed to accept str objects.
        :param kwargs: see the InputHandler base class for more details.
        """
        super().__init__(**kwargs)
        self.file: str = kwargs.get('file')
        if self.file is None:
            raise ValueError('file is mandatory')
        self.delimiter: str = kwargs.get('delimiter', ',')
        self.parsers: dict[str, Callable[[str], Any]] = kwargs.get('parsers', dict())

    def run(self):
        with open(self.file, newline='') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=self.delimiter)
            for t, port, msg in csv_reader:
                try:
                    time.sleep(float(t))
                except ValueError:  # unable to cast to float -> probably header, ignore it
                    continue
                # if parser is not defined, we forward the message as is (i.e., in string format)
                self.queue.put((port, self.parsers.get(port, lambda x: x)))
