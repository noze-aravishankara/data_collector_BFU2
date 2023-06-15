#!/usr/bin/env python3

"""
Company     : NOZE
Author      : Eddy Fraga
Created on  : January 20, 2023
File type   : python
File name   : serialComm.py
Description : Python interface class allowing access to the serial communication interface.
Reference   : N/A
"""

from time import sleep

import serial
from serial.tools.list_ports import comports
from serial.serialutil import SerialException
import logging
from .constants import bfuCommand, bfuTiming, endMsg
logging.basicConfig(level=logging.DEBUG)




class SerialComm:

    def __init__(self, port, baud_rate=115200):

        try:
            self.port = serial.Serial(port, baud_rate)
            if self.port.is_open:
                pass
            else:
                self.port.open()
            logging.info(f'Port {port} is open, running at baudrate: {baud_rate}')
            self.port_status = True
        
        except SerialException as e:
            logging.info(f"Error - Can't open {port}. Only these ports are available: \n{self.display_available_port()}")
            self.port_status = False

        # self.port = serial.Serial(port, baud_rate)
        # self.port_status = True
        self.delimiter = endMsg.END_NVM_LINE
        logging.info('Done device setup')

    def get_status(self):
        return self.port_status

    def display_available_port(self):
        idx = 1
        for port in comports():
            print(idx, ")", port)
            idx += 1

    def data_available(self):
        if self.port.in_waiting > 0:
            return True
        return False

    def wait_for_data(self):
        timeout = 0
        while not self.data_available() and timeout < bfuTiming.SERIAL_TIMEOUT_DELAY_SEC:
            sleep(bfuTiming.SERIAL_WAIT_DELAY_SEC)
            timeout = timeout + bfuTiming.SERIAL_WAIT_DELAY_SEC
        if timeout >= bfuTiming.SERIAL_TIMEOUT_DELAY_SEC:
            print("Error - Serial data Timeout!")
            return False
        return True

    def write_data(self, write_data):
        self.port.write(write_data.encode())

    def write_data_with_response(self, tx_msg):
        self.port.write(tx_msg.encode())
        if self.wait_for_data() is False:
            return False
        rx_msg = self.get_data_until(endMsg.END_PAYLOAD)
        print("Response : ", tx_msg, " ==> ", rx_msg)
        if str(bfuCommand.SUCCESS_RESULT) in str(rx_msg) is False:
            print("Response failure : ", tx_msg, " ==> ", rx_msg)
            return False
        return True
    
    def get_data(self):
        if self.data_available():
            rx_data = str(self.port.read_until(self.delimiter).decode('utf-8'))
            #rx_data = str(self.port.read_until(self.delimiter))
            rx_data = rx_data.replace("\n", "")
            rx_data = rx_data.replace("\r", "")
            rx_data = rx_data.replace('\x00', '')
            rx_data = rx_data.replace("'", "\"")
            return rx_data
        return None

    def flush_all_input_data(self):
        while self.data_available():
            self.port.read()


if __name__ == '__main__':
    port = SerialComm('/dev/ttyACM1')
