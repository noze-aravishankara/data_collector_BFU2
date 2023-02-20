import json
import logging
import sys

from .constants import endMsg
from .serialComm import SerialComm

logging.basicConfig(level=logging.INFO)


class BFU:
    def __init__(self, port='COM5', baudrate=115200, name='BFU1s'):
        self.port = port
        self.baudrate = baudrate
        self.name = name

        self.trial_state = 'pre-baseline'
        self.data_collection_status = False

        try:
            self.device = self.connect_to_device()
            logging.info(f'Successfully connected to {self.name} on {self.port}')
        except:
            print(f'Could not connect. Port: {self.port} is not available.')
            sys.exit()

        self.array = []
        self.shape_headers()
        logging.debug(self.headers)

    def connect_to_device(self):
        return SerialComm(self.port, self.baudrate)

    def get_new_data(self):
        while not self.device.data_available():
            pass
        else:
            _ = json.loads(self.device.get_data_until(endMsg.END_NVM_LINE))
            logging.debug(_)
        return _

    def get_new_values(self):
        self.shape_data(self.get_new_data())

    def shape_headers(self):
        _ = self.get_new_data()
        _ = [list(d.keys())[0] for d in _['t']]
        _.append('Trial State')
        self.headers = _

    def shape_data(self, data):
        _ = [list(d.values())[0] for d in data['t']]
        _.append(self.trial_state)
        logging.debug(_)
        self.array.append(_)

    def get_array(self):
        return self.array

    def get_array_shape(self):
        return len(self.array)

    # def range_collection(self, num_runs):
    #     for i in range(num_runs):
    #         self.get_new_data()
    #         logging.info(f'Array len: {self.get_array_shape()}')

    def continuous_collection(self):
        while self.data_collection_status:
            self.get_new_values()
            logging.debug(f'Array len: {self.get_array_shape()}')
        logging.info(f"Exiting Continuous Data Collection Loop for {self.name}")
        logging.debug(self.array)


if __name__ == '__main__':
    A = BFU('COM5', 115200, 'BFU1')
    B = A.range_collection(10)
    print(B)