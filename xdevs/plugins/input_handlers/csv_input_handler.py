import csv
import time

from xdevs.rt_sim.input_handler import InputHandler


class CSVInputHandler(InputHandler):
    def __init__(self, file, **kwargs):
        super().__init__(**kwargs)
        self.file = file
        if self.file is None:
            raise ValueError('file is mandatory')
        self.data = list()
        self.reader = None
        self.csv_file = None

    def initialize(self):
        self.csv_file = open(self.file, 'r')
        self.reader = csv.DictReader(self.csv_file)
        i = 0
        for row in self.reader:
            self.data.append(list())
            for field in self.reader.fieldnames:
                self.data[i].append(row[field])
            i = i + 1

    def exit(self):
        self.csv_file.close()

    def run(self):

        for row in self.data:
            time.sleep(int(row[0]))
            self.queue.put((row[1], row[2]))
