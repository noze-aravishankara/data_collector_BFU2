import csv
import logging

logging.basicConfig(level=logging.INFO)


class data_manager:
    def __init__(self, fname, log_level=logging.INFO):
        self.fname = fname
        self.create_file()

    def create_file(self):
        with open(f'{self.fname}', 'w', newline='') as f:
            f.close()
        logging.debug(f'Created file {self.fname}')

    def append_file(self, data):
        with open(f'{self.fname}', 'a', newline='') as f:
            logging.debug('Opening file')
            csv_writer = csv.writer(f, delimiter=',')
            csv_writer.writerow(data)
            f.close()
        logging.debug('Done appending file.')

