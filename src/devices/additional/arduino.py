from enum import Enum
import os
import serial
import threading
import time
import sys

import numpy as np
import serial
from serial.tools import list_ports

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from utility.logger import get_logger
from utility.time_utils import get_unix_timestamp
from devices.base_device import ABCDevice


_BUFFER_SIZE = 20


class Status(Enum):
    UNINITIALIZED = 0
    RUNNING = 2
    PAUSED = 3
    STOPPED = 4
    TERMINATED = 5
    DISCONNECTED = 6


class Arduino(ABCDevice):
    """
    """
    name = "arduino"
    __instance = None
    

    @staticmethod
    def get_instance():
        """Static access method.
        """
        if Arduino.__instance == None:
            Arduino()
        return Arduino.__instance

    def __init__(self):
        """Virtually private constructor.
        """
        if Arduino.__instance is not None:
            return None
        else:
            Arduino.__instance = self
            self._status = Status.UNINITIALIZED
            self._last20 = [.0]*_BUFFER_SIZE

    #@abc.abstractmethod
    def initialize(self, connection_port, column_headers=["Arduino"], baudrate=9600, timeout=10, target_temperature=30):
        """This method is responsible for initialization of the device.
        """
        try:
            Arduino.headers = column_headers
            self._location = connection_port
            self._baudrate = baudrate
            self._timeout = timeout
            self._connection = serial.Serial(connection_port, baudrate=baudrate, timeout=timeout)
            self._run_thread = threading.Thread(target=self._start_collection)
            self._run_thread.start()
            get_logger().info("Successfully connected to Arduino at port {}.".format(connection_port))
            return True
        except Exception as e:
            get_logger().warning("Failed to create device connected to port {} due to :\n {}".format(connection_port, e))
            return False

    def _start_collection(self):
        """This method is responsible for beginning collection.
        """
        self._status = Status.RUNNING
        while(self._status == Status.RUNNING):
            try:
                x = self._connection.readline()            
                self.add_value(x.decode("utf-8"))
            except:
                self.add_value(float(-1))
                get_logger().warning("Device at {} disconnected.  Reconnect device.".format(self._location))
                self._reconnect_to_serial_port(self._location)

    def get_required_arguments_to_build(self):
        return {"connection": None, "baudrate": 9600, "timeout": 2}

    def _reconnect_to_serial_port(self, port_location):
        """

        """
        time.sleep(4)
        get_logger().info("Re-connecting lost serial port ...")
        try:
            connection_port = port_location
            if connection_port:
                self._connection = serial.Serial(connection_port, baudrate=self._baudrate, timeout=self._timeout)
                get_logger().info("Successfully reconnected to the port {}.\n\n".format(self._location))
        except serial.serialutil.SerialException as e:
            get_logger().debug("Exception while re-connecting {}".format(e))
            time.sleep(10)

    def get_header(self):
        """This method is responsible for returning the specifications of the device.
        """
        pass

    @staticmethod
    def get_data_info():
        """This method is responsible for returning the information regarding elements in data list received from the device.
            NOTE: Subclasses must implement this as a @staticmethod.
        """
        return Arduino.headers

    def get_data(self):
        """This method is responsible for fetching the data from the device and returning a list containing all the data received
            from the device and not been sent.
        """
        return self._last20[-1]

    def terminate(self):
        """This method is responsible for termination of the connection and also taking required measurements to dsipose the device object..
        """
        self._status = Status.STOPPED
        time.sleep(1)
        get_logger().info("Closing the Arduino sensor connected to {}".format(self._connection.port))
        self._connection.close()
        self._status = Status.TERMINATED

    def add_value(self, value):
        self._last20.append(value)
        del self._last20[0]
