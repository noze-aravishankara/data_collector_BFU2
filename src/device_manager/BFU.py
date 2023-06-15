import json
import logging
import sys
import threading

from .constants import endMsg
from .serialComm import SerialComm
from .data_manager import data_manager as dm

logging.basicConfig(level=logging.INFO)


class BFU:
    def __init__(self, port='COM5', baudrate=115200, name='BFU1s', fname='../../output/BASE.csv', log_level=logging.INFO):
        self.port = port
        self.baudrate = baudrate
        self.name = name
        # logging.basicConfig(level=log_level)

        self.trial_state = 'pre-baseline'
        self.data_collection_status = False

        try:
            self.device = self.connect_to_device()
            logging.info(f'Successfully connected to {self.name} on {self.port}')
        except:
            print(f'Could not connect. Port: {self.port} is not available.')
            sys.exit()

        self.file_setup(fname)
        self.update_file_with_headers()
        logging.debug('Added headers')
        # self.array = []

    def connect_to_device(self):
        return SerialComm(self.port, self.baudrate)

    def file_setup(self, fname):
        self.dm = dm(fname)

    def update_file(self, data):
        _ = threading.Thread(target=self.dm.append_file, args=(data,))
        _.start()
        logging.debug('Updated CSV file')

    def get_new_data(self):
        while not self.device.data_available():
            pass
        else:
            _ = json.loads(self.device.get_data_until(endMsg.END_NVM_LINE))
            logging.debug(_)
        return _

    def get_new_values(self):
        self.update_data(self.get_new_data())

    def update_file_with_headers(self):
        _ = self.get_new_data()
        _ = ["Serial Number"]+[list(d.keys())[0] for d in _['t']]
        _.append('Trial State')
        self.update_file(_)

    def update_data(self, data):
        _ = [data["sn"]]+[list(d.values())[0] for d in data['t']]
        _.append(self.trial_state)
        logging.debug(_)
        self.update_file(_)

    def continuous_collection(self):
        while self.data_collection_status:
            self.get_new_values()
        logging.info(f"Exiting Continuous Data Collection Loop for {self.name}")


if __name__ == '__main__':
    A = BFU('COM5', 115200, 'BFU1')
    B = A.range_collection(10)
    print(B)