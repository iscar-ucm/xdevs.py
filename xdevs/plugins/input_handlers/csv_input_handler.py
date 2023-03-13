import csv
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
            for row in csv_reader:
                # t = row[0], port = row[1], msg = row[2]
                try:
                    if len(row) < 3 or row[1] == '':
                        # if row[2] = msg = '', '' will be inserted. No ValueError for msg = ''
                        raise ValueError('Format of file is wrong. '
                                         'Each row must have at least 3 values: t, port, and msg.')
                    else:
                        try:
                            time.sleep(float(row[0]))
                        except ValueError:  # unable to cast to float -> probably header, ignore it
                            continue
                        # if parser is not defined, we forward the message as is (i.e., in string format)
                        self.queue.put((row[1], row[2] if self.parsers is None else self.parsers.get(row[1])(row[2])))
                except ValueError as e:
                    print(f'Error in {self.file}: {e} Skipping row {row}')
                    continue
