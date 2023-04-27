import csv
import sys
import time
from xdevs.rt_sim.input_handler import InputHandler


class CSVInputHandler(InputHandler):
    def __init__(self, **kwargs):
        """
        CSVInputHandler reads a file and insert the messages in the corresponding port of the system.

        File must contain 3 columns:

            1st -> t, is for the time between the messages are inserted in the system. t = 0 or '' , no time is waited.

            2nd -> port, is for specifying the port name. Port = '' ,the row will be omitted.

            3rd -> msg, is for inserting the message which will be transmitted.

        :param str file: CSV file path.
        :param str delimiter: column delimiter in CSV file. By default, it is set to ','.
        """
        super().__init__(**kwargs)
        self.file: str = kwargs.get('file')
        if self.file is None:
            raise ValueError('file is mandatory')
        self.delimiter: str = kwargs.get('delimiter', ',')

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
                # 4. inject event to queue
                self.push_msg(port, msg)
