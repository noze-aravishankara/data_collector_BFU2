from enum import Enum
import os
import serial
import threading
import time
import sys
from utility.file_utils import read_yaml_file
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


def initialize_temperature_controller():
    """
    Read and set TEMPERATURE_STEPS from temperature.yml file and establish a servo motor class obj -> TEMPERATURE_CONTROLLER.
    """
    file_name = os.path.join(os.getcwd(), "temperature.yml")
    content = read_yaml_file(file_name)

    BmeSensor.TEMPERATURE_CONTROLLER = serial.Serial(content["port"], baudrate=9600,
                                                     timeout=1)
    del content["port"]

    for trial, temperature in content.items():
        BmeSensor.TEMPERATURE_STEPS[trial] = {"temperature": temperature, "temp_set": False}

    get_logger().info(BmeSensor.TEMPERATURE_STEPS)


class BmeSensor(ABCDevice):
    """
    """
    name = "bme"

    TEMPERATURE_CONTROLLER = None
    TEMPERATURE_STEPS = {}

    def __init__(self):
        """Virtually private constructor.
        """
        BmeSensor.__instance = self
        self._status = Status.UNINITIALIZED
        self._last20 = [.0] * _BUFFER_SIZE

        # if BmeSensor.TEMPERATURE_CONTROLLER is None:
        #     initialize_temperature_controller()

    def shift_temperature(self, from_t, new_trial_id):
        """
        takes current Temperature "from_t" and sets it to new temperature based on trial_id from TEMPERATURE_STEPS
        """
        if BmeSensor.TEMPERATURE_CONTROLLER is None:
            return

        next_temp = BmeSensor.TEMPERATURE_STEPS["trial_{}".format(new_trial_id)]
        # get_logger().info("next temp : {} from temp: {}".format(not(next_temp["temp_set"]), from_t))

        def roundint(value, base=5):
            return int(value) - int(value) % int(base)

        def temperature_cmd(current_temp, new_temp):
            current_temp = roundint(current_temp)
            new_temp = roundint(new_temp)
            if current_temp > new_temp:
                direction = 'D'
            else:
                direction = 'U'

            delta_t = str(int(abs(from_t - new_temp)))
            steps = '<{},{}>'.format(direction, delta_t)
            get_logger().info("steps: {}".format(steps))
            return direction, delta_t

        direction, change_temp = temperature_cmd(from_t, next_temp["temperature"])

        if (int(change_temp) > 0) and (not (next_temp["temp_set"])):
            steps = '<{},{}>'.format(direction, change_temp)
            get_logger().info("Changing temp from: {} to {} for trial_id: {}".format(from_t, next_temp, new_trial_id))
            BmeSensor.TEMPERATURE_CONTROLLER.write(steps.encode())
            next_temp["temp_set"] = True
        else:
            pass

        # print("SERIAL STRING")

    # @abc.abstractmethod
    def initialize(self, connection_port, column_headers=["BmeSensor"], baudrate=9600, timeout=10,
                   target_temperature=30,temperature_control= False):
        """This method is responsible for initialization of the device.
        """
        try:
            self._headers = column_headers
            self._location = connection_port
            self._baudrate = baudrate
            self._timeout = timeout
            self._connection = serial.Serial(connection_port, baudrate=baudrate, timeout=timeout)
            self._run_thread = threading.Thread(target=self._start_collection)
            self._control_enabled = temperature_control

            if self._control_enabled and BmeSensor.TEMPERATURE_CONTROLLER is None:
                initialize_temperature_controller()

            self._run_thread.start()
            get_logger().info("Successfully connected to BmeSensor at port {}.".format(connection_port))
            return True
        except Exception as e:
            get_logger().warning(
                "Failed to create device connected to port {} due to :\n {}".format(connection_port, e))
            return False

    def _start_collection(self):
        """This method is responsible for beginning collection.
        """
        self._status = Status.RUNNING
        while self._status == Status.RUNNING:
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

    def get_data_info(self):
        """This method is responsible for returning the information regarding elements in data list received from the device.
            NOTE: Subclasses must implement this as a @staticmethod.
        """
        return self._headers

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
        get_logger().info("Closing the BmeSensor sensor connected to {}".format(self._connection.port))
        self._connection.close()
        if BmeSensor.TEMPERATURE_CONTROLLER:
            BmeSensor.TEMPERATURE_CONTROLLER.close()
        self._status = Status.TERMINATED

    def add_value(self, value):
        self._last20.append(value)
        del self._last20[0]
