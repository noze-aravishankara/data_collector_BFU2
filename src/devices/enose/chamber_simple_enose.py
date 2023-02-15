import copy
from enum import Enum
import os
from queue import Queue
import struct
import sys
import threading
from threading import Condition
import time

import numpy as np
import serial
from serial.tools import list_ports

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from utility.logger import get_logger
from utility.time_utils import get_unix_timestamp
from devices.base_device import ABCDevice

POLYMER_COUNT = 32
POLYMER_DATA_INDEX = 1
ADDITIONAL_DATA = [("timestamp_ms", get_unix_timestamp)]
RECONNECT_DELAY = 4
DEFAULT_TEMPERATURE = 30
MAXIMUM_TEMPERATURE = 48

_PAYLOAD_STRUCTURE = [("precision_resistor", 0)] + \
                     [("s{}".format(i), i + POLYMER_DATA_INDEX) for i in range(1, POLYMER_COUNT + 1)] + \
                     [("temperature", POLYMER_DATA_INDEX + POLYMER_COUNT)] + \
                     [("humidity", POLYMER_DATA_INDEX + POLYMER_COUNT + 1)] + \
                     [("deviceid", POLYMER_DATA_INDEX + POLYMER_COUNT + 2)]
                     # [("chamberid", POLYMER_DATA_INDEX + POLYMER_COUNT + 3)]

_PAYLOAD_LENGTH = len(_PAYLOAD_STRUCTURE)


class Status(Enum):
    UNINITIALIZED = 0
    RUNNING = 2
    PAUSED = 3
    STOPPED = 4
    TERMINATED = 5
    DISCONNECTED = 6


class ChamberSimpleENose(ABCDevice):
    """

    """
    name = "chamber_simple_enose"

    def __init__(self):
        self._status = Status.UNINITIALIZED
        self._data_buffer_lock = threading.Lock()
        self._data_buffer = []
        self._baseline_reading = []
        self._device_id = ""
        self._chamber_id = ""

    def initialize(self, connection_port, baudrate=9600, timeout=2, target_temperature=30,chamber_id ="0"):
        """This method is responsible for initialization of the device.
        """
        try:
            self._location = next(cp.location for cp in list_ports.comports() if cp.device == connection_port)
            self._baudrate = baudrate
            self._stable = False
            self._chamber_id = chamber_id
            self._update_baseline_reading = False
            self._connection = self._initialize_serial_port(connection_port, baudrate=baudrate, timeout=timeout)
            self._target_temperature = self._set_target_temperature(target_temperature)
            self._reader_th = threading.Thread(target=self._processor)
            self._reader_th.setDaemon(True)
            self._reader_th.start()
            return True
        except Exception as e:
            get_logger().warning("Failed to create device connected to port {} due to:\n {}".format(connection_port, e))
            return False

    def _initialize_serial_port(self, connection_port, baudrate, timeout):
        conn = serial.Serial(connection_port, baudrate=baudrate, timeout=timeout)
        time.sleep(1)
        conn.flushInput()
        conn.flushOutput()
        conn.write(1)
        time.sleep(0.2)
        get_logger().info("Successfully connected to serial port {}.".format(connection_port))
        return conn

    def _set_target_temperature(self, target_temperature):
        if target_temperature > MAXIMUM_TEMPERATURE:
            get_logger().warning(
                "Target temperature {} is higher that the maximum temperature!\nSetting temperature to {}".format(
                    target_temperature, MAXIMUM_TEMPERATURE))
            target_temperature = MAXIMUM_TEMPERATURE
        self._connection.write((str(target_temperature) + "\r\n").encode())
        # To get the string sent by the device regarding temperature being set.
        msg = self._connection.readline()
        msg = self._connection.readline()
        get_logger().info("Temperature is set to {} for port {}".format(target_temperature, self._connection.port))
        return target_temperature

    def _processor(self, time_delay=0.1):
        time.sleep(0.3)
        self._status = Status.RUNNING
        while self._status not in (Status.STOPPED, Status.TERMINATED):
            time.sleep(time_delay)
            if self._status in (Status.RUNNING, Status.PAUSED):
                self._read_data()
            elif self._status is Status.DISCONNECTED:
                self._connection = self._reconnect_to_serial_port(self._location)

    def _read_data(self):
        """This method is responsible for fetching the data from the device and returning a list containing all the data received
            from the device and not been sent.
        """
        try:
            data = []
            raw_data = self._connection.readline().decode("utf-8")
            data = self._decode_data(raw_data) + \
                   [v[1]() for v in ADDITIONAL_DATA]
            # data = np.append(data, [v[1]() for v in ADDITIONAL_DATA])
            self._data_buffer_lock.acquire()
            if self._status is Status.RUNNING and len(data) == len(_PAYLOAD_STRUCTURE) + len(ADDITIONAL_DATA):
                # get_logger().info("Received data from {}.".format(self._connection.port))
                data_without_id = data
                self._data_buffer.append(data_without_id)
        except serial.serialutil.SerialException as e:
            self._status = Status.DISCONNECTED
            get_logger().error("Serial connection {} exception: {}".format(self._connection.port, e))
        except Exception as e:
            get_logger().warning("Exception happened while getting data from {}:\n{}".format(
                self._connection.port, e))
        finally:
            if self._data_buffer_lock.locked():
                self._data_buffer_lock.release()

    def _decode_data(self, data):
        """

        """
        try:
            if not data:
                return []
            splitted = data.split("\t")[:-1]
            # get_logger().info(splitted)
            values = np.array(splitted[:-1], dtype=np.float)

            self._device_id = splitted[-1]

            self._device_id = splitted[-1]

            # self._chamber_id = splitted[-1][:-1]
            # values = values.tolist() + [self._device_id] + [self._chamber_id]
            values = values.tolist() + [self._device_id]

            if len(values) < len(_PAYLOAD_STRUCTURE):
                raise Exception("Invalid packet {} received from port {}".format(data, self._connection.port))
            return values
        except Exception as e:
            get_logger().warning("Cannot decode data:\n{}\n due to:\n {}".format(data, e))
            return []

    def _reconnect_to_serial_port(self, port_location):
        """

        """
        time.sleep(RECONNECT_DELAY)
        get_logger().info("Re-connecting lost serial port ...")
        conn = None
        try:
            connection_port = next(cp.device for cp in list_ports.comports() if \
                                   cp.location == port_location)
            connection_port
            if connection_port:
                conn = self._initialize_serial_port(connection_port, self._baudrate, 2)
                self._data_buffer_lock.acquire()
                self._data_buffer = []
                self._baseline_reading = []
                self._data_buffer_lock.release()
                self._set_target_temperature(self._target_temperature)
                self._status = Status.RUNNING
                get_logger().info("Successfully reconnected to the port {}.\n\n".format(conn.name))
        except serial.serialutil.SerialException as e:
            get_logger().debug("Exception while re-connecting {}".format(e))
            time.sleep(10)
        finally:
            return conn

    def get_required_arguments_to_build(self):
        """
        """
        return {"connection": None, "baudrate": 9600, "timeout": 2, "target_temperature": 30}

    def get_header(self):
        """This method is responsible for returning the specifications of the device.
        """
        return ["device_id", "simple_firmware", "0.0"]

    @staticmethod
    def get_data_info():
        """This method is responsible for returning the information regarding elements in data list received from the device.
            NOTE: Subclasses must implement this as a @staticmethod.
        """
        data_info = [p[0] for p in _PAYLOAD_STRUCTURE]
        data_info.extend([ad[0] for ad in ADDITIONAL_DATA])
        return data_info

    def get_data(self, flush_buffer=True):
        data = []
        try:
            self._data_buffer_lock.acquire()
            data = self._data_buffer[:]
            if self._update_baseline_reading:
                self._baseline_reading = copy.deepcopy(data)[0][1:35]
                get_logger().info("deivce_id: {}".format(self._device_id))
                get_logger().info("updated baseline_reading: {}".format(self._baseline_reading))
                self._update_baseline_reading = False
            self._data_buffer_lock.release()

            if flush_buffer:
                self._data_buffer = []
        except Exception as e:
            get_logger().warning("Failed to get data from {} due to {}".format(self._connection.port, e))
        return data

    def compare_readings(self, data, signal_threshhold=2.0, humidity_threshold=2.0):
        try:
            last_reading = np.array(self._baseline_reading)
            current_reading = np.array(data)

            difference_array = np.absolute(np.subtract(current_reading, last_reading))

            percent_change_array = np.divide(difference_array, last_reading) * 100

            delta_change_array = percent_change_array < signal_threshhold

            if all(delta_change_array):
                self._stable = True
                get_logger().info("signal is stable")

            get_logger().info("deivce_id: {}".format(self._device_id))
            # get_logger().info("last_reading: {}".format(last_reading))
            # get_logger().info("current_reading: {}".format(current_reading))
            # get_logger().info("percent_change: {}".format(percent_change_array))
            get_logger().info("delta_change_array: {}".format(delta_change_array))

            # self._stable = True

        except RuntimeWarning:
            get_logger().warning("0 value encountered from reading ")
            self._stable = False


        except Exception as e:
            get_logger().warning("Failed to calculate percent change due to {}".format(e))
            self._stable = False

    def get_stability(self, data):
        """
        we need to compare the baseline_reading to the data in the data_buffer,
        if we use get_data method there,however, make sure not to flush the buffer!
        need another method to compare two states and updates the self._stable variable
        """
        data = data[1:35]
        self.compare_readings(data)
        """
        updating the baseline_reading should be last thing that this method doess so that it updates 
        to the new baseline reading
        """
        self._update_baseline_reading = True
        # self._baseline_reading = []
        stable = self._stable

        return stable

    def terminate(self):
        """This method is responsible for termination of the connection and also taking required measurements to dispose the device object.
        """
        self._status = Status.STOPPED
        time.sleep(1)
        get_logger().info("Closing the enose connected to {}".format(self._connection.port))
        self._connection.close()
        self._status = Status.TERMINATED
