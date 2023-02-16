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

        group = asyncio.gather([self.stupid_printer(), self.data_collector()])
        asyncio.run(group)

    async def stupid_printer(self):
        while True:
            await print("Hello Stupid")

    async def serial_waiter(self):
        while not self.device.data_available():
            pass

    async def data_collector(self):
        await self.serial_waiter()
        self.now = datetime.now()
        logging.info(self.now - self.start_time)
        self.start_time = self.now
        return json.loads(self.device.get_data_until(endMsg.END_NVM_LINE))

    def test_data(self):
        A = self.read_data_from_device()
        C = [list(d.values()) for d in A['t']]
        print(C)

    def run_loop(self):
        while True:
            F = self.read_data_from_device()
            G = list([element.values() for element in F])
            print(G)



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

