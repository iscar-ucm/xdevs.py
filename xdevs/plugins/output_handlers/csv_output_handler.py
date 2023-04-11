import csv
import time
from xdevs.rt_sim.output_handler import OutputHandler


class CSVOutputHandler(OutputHandler):
    def __init__(self, **kwargs):
        """
        CSVOutputHandler store in a file the outgoing events in the form : time, port, msg.
        If not file is given, a default file is created by the name csv_output_date_time.csv.

        :param output_file: path or name of the output file. By default, it is set to 'output.csv'
        :param str delimiter: column delimiter in CSV file. By default, it is set to ','.
        """
        super().__init__()
        self.file = kwargs.get('file', 'output.csv')  # better to have a fixed name for automation
        self.delimiter: str = kwargs.get('delimiter', ',')

    def run(self):
        initial_time = time.time()
        # in general, it is not a good idea to append to an existing file when logging a simulation
        with open(self.file, 'w', newline='') as file:
            writer = csv.writer(file, delimiter=self.delimiter)
            writer.writerow(("t", "port", "msg"))
            while True:
                port, msg = self.queue.get()  # blocks indefinitely until it receives a message
                writer.writerow((time.time() - initial_time, port, msg))
                file.flush()
        # no need to close the file, the with open block does the trick
