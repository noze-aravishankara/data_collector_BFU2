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
from .processBFU import processBfu
from .serialComm import SerialComm


class BFU_RUNNER:
    def __init__(self, com_port):
        self.com_port = com_port
        self.BFU = processBfu(self.com_port)
        if not self.BFU.get_port_status():
            sys.exit()
        self.BFU.display_telemetry(True)


    def process_bfu_communication(self):
        bfu = processBfu(self.com_port)
        if bfu.get_port_status() is False:
            sys.exit()
        bfu.display_telemetry(True)


if __name__ == "__main__":
    BFU_RUNNER('COM3')
