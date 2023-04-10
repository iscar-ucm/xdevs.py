import csv
import queue
import time
import datetime

from xdevs.rt_sim.output_handler import OutputHandler


class CSVOutputHandler(OutputHandler):
    def __init__(self, **kwargs):
        """
        CSVOutputHandler store in a file the outgoing events in the form : Port, p_type.
        If not output_file is given, a default file is created by the name csv_output_date_time.csv.

        :param output_file: path or name of the file in which the data is going to be store.
        """
        super().__init__()
        self.csv_queue = self.queue

        self.output_file = kwargs.get('output_file', None)
        if self.output_file is None:
            self.output_file = 'csv_output_'+datetime.datetime.now().strftime('%d%m%Y_%H%M%S')+'.csv'

    def run(self):
        while True:
            # First we check for outgoing events
            try:
                row = self.csv_queue.get()
            except queue.Empty:
                continue
            # If an outgoing event occurs we append it to the last line of the file.
            if row is not None:
                with open(self.output_file, 'a+', newline='') as csv_file:
                    writer = csv.writer(csv_file)
                    writer.writerow(row)

                csv_file.close()
                row = None
