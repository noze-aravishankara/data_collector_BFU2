#!/usr/bin/env python3

"""
Company     : NOZE
Author      : Eddy Fraga
Created on  : January 20, 2023
File type   : python
File name   : BFU_RUNNER.py
Description : Main python script used to interact with the BFU MSP430 module.
Reference   : N/A
"""

import sys
#from .processBFU import processBfu
from .serialComm import SerialComm
from .constants import endMsg, jsonInfo
import json
from datetime import datetime as dt
import logging

logging.basicConfig(level=logging.INFO)


class BFU_RUNNER:
    def __init__(self, com_port, name):
        self.com_port = com_port
        self.BFU = self.connect_to_port()
        self.name = name

        if not self.get_port_status():
            sys.exit()

        self.set_trial_state('baseline')
        print(f'Created device: {self.name}')
        self.create_data_array()

    def connect_to_port(self):
        return SerialComm(self.com_port)

    def get_port_status(self):
        return self.BFU.get_status()

    def get_data_keys(self, data):
        if data is not None:
            return data.keys()
        else:
            return None

    def get_data_values(self, data):
        if data is not None:
            return data.values()
        else:
            return None

    def flush_serial_port(self):
        self.BFU.flush_all_input_data()

    def get_new_data(self):
        while not self.BFU.data_available():
            pass
        else:
            self.now = dt.now()
            logging.info('New Data Point')
            self.start_time = self.now

            _ = json.loads(self.BFU.get_data_until(endMsg.END_NVM_LINE))
            _ = [list(d.values()) for d in _['t']]
            _.append(self.trial_state)
            self.array.append(_)

    def create_data_array(self):
        self.array = []

    def set_trial_state(self, state):
        self.trial_state = state

    def update_array(self):
        _ = self.get_data_values(self.get_new_data())
        _.append(self.trial_state)
        self.array.append(_)

    def get_complete_array(self):
        _ = self.array
        return _

    def continuous_data_collector(self):
        while self.data_collection_status:
            self.get_new_data()




if __name__ == "__main__":
    BFU_RUNNER('COM3')
