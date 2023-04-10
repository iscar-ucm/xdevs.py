import csv
import sys
import time
from typing import Callable, Any
from xdevs.rt_sim.input_handler import InputHandler


class CSVInputHandler(InputHandler):
    def __init__(self, **kwargs):
        """
        CSVInputHandler reads a file and insert the messages in the corresponding port of the system.

        File must contain 3 columns:

            1st -> t, is for the time between the messages are inserted in the system. t = 0 or '' , no time is waited.

            2nd -> port, is for specify the port name. Port = '' ,the row will be omitted.

            3rd -> msg, is for inserting the message which will be transmitted.

        :param str file: CSV file path.
        :param str delimiter: column delimiter in CSV file. By default, it is set to ','.
        :param dict[str, Callable[[str], Any]] parsers: message parsers. Keys are port names, and values are functions
        that take a string and returns an object of the corresponding port type. If a parser is not defined, this
        input handler assumes that the port type is str and forward the message as is. By default, all the ports
        are assumed to accept str objects.
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
            for i, row in enumerate(csv_reader):
                # 1. unwrap row
                try:
                    t, port, msg, *_others = row
                except ValueError:
                    print(f'LINE {i + 1}: invalid row ({row}). Rows must have 3 columns:'
                          ' t, port, and msg. Row will be ignored', file=sys.stderr)
                    continue
                # 2. sleep
                try:
                    time.sleep(float(t))
                except ValueError:
                    if i != 0:  # To avoid logging an error while parsing the header
                        print(f'LINE {i + 1}: error parsing t ("{t}"). Row will be ignored', file=sys.stderr)
                    continue
                # 3. make sure that port is not empty
                if not port:
                    print(f'LINE {i + 1}: port ID is empty. Row will be ignored', file=sys.stderr)
                    continue
                # 4. parse message
                try:
                    # if parser is not defined, we forward the message as is (i.e., in string format)
                    msg = self.parsers.get(port, lambda x: x)(msg)
                except Exception:
                    print(f'LINE {i + 1}: error parsing msg ("{msg}"). Row will be ignored', file=sys.stderr)
                    continue
                # 5. inject event to queue
                self.push_to_queue(port, msg)
