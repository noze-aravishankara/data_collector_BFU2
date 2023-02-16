import json
from time import sleep

from .constants import bfuCommand, nvmInfo, endMsg, bfuTiming, jsonInfo
from .serialComm import SerialComm


class processBFU:

    telemetry_msg_status = True
    status = True

    def __init__(self, com_port):
        self.com_port = com_port
        self.port = SerialComm(self.com_port)

    def get_port_status(self):
        return self.port.get_status()

    def get_data_keys(self, data):
        return data.keys()

    def get_data_values(self, data):
        return data.values()


