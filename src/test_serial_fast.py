from device_handler.serialComm import SerialComm
import json
from device_handler.constants import *
from datetime import datetime
import logging
import numpy as np

import asyncio
logging.basicConfig(level=logging.INFO)


class DEVICE:
    def __init__(self, com_port, baud_rate=115200):
        self.com_ = com_port
        self.device = SerialComm(self.com_, baud_rate)
        self.data = []

        self.start_time = datetime.now()
        #self.run_loop()
        self.test_data()

    def test_data(self):
        A = self.read_data_from_device()
        C = [list(d.values()) for d in A['t']]
        print(C)

    def run_loop(self):
        while True:
            F = self.read_data_from_device()
            #print(type(F))
            G = list([element.values() for element in F])
            print(G)
            #print([list(d.values() for d in list(F.values()))])
            #print([list(d.values() for d in F)])


    def read_data_from_device(self):
        while not self.device.data_available():
            pass
        else:
            self.now = datetime.now()
            logging.info(self.now - self.start_time)
            self.start_time = self.now
            return json.loads(self.device.get_data_until(endMsg.END_NVM_LINE))


if __name__ == '__main__':
    A = DEVICE('COM3', 115200)

