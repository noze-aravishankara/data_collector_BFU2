import copy
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
import time
from datetime import datetime

_BUFFER_SIZE = 20


class Status(Enum):
    UNINITIALIZED = 0
    RUNNING = 2
    PAUSED = 3
    STOPPED = 4
    TERMINATED = 5
    DISCONNECTED = 6


class Autosampler(ABCDevice):
    """
    """
    name = "autosampler"
    _AutoSamplerStatusBuffer = [""] * _BUFFER_SIZE
    SAMPLER_STATE = "baseline_STATE"
    MFC_STATE_EXEC_LENGTH = 0
    TRIAL_ID = 1
    PROTOCOL = {}
    # TRIAL_STATE = {}
    TRIGGER_REQUIRED = False
    state_buffer_lock = threading.Lock()

    # Axis movements (mm)
    x_travel = 825
    y_travel = 125
    z_travel = 350
    e_travel = 500

    # Linear movement feedrate G0 (mm/min)
    feedrate = 60000

    # Stepper movement calibration M92 (steps/mm)
    x_steps_per_unit = 80
    y_steps_per_unit = x_steps_per_unit
    z_steps_per_unit = 1600
    e_steps_per_unit = x_steps_per_unit

    # Axis max feedrates M203 (mm/sec)
    x_max_feedrate = 1000
    y_max_feedrate = 300
    z_max_feedrate = 10
    e_max_feedrate = x_max_feedrate

    # Axis acceleration M201 (mm/sec/sec)
    x_accel = 50
    y_accel = x_accel
    z_accel = 10
    e_accel = x_accel

    # Axis limits (mm)
    x_min = 0
    y_min = 0
    z_min = 0
    e_min = 0

    x_max = 500
    y_max = 500
    z_max = 500
    e_max = 500

    def __init__(self):
        """Virtually private constructor."""

        Autosampler.__instance = self
        self._status = Status.UNINITIALIZED
        self._last20 = [""] * _BUFFER_SIZE
        self._protocol_data_buffer_lock = threading.Lock()

    # @abc.abstractmethod
    def initialize(self, connection_port, column_headers=["Autosampler"], baudrate=115200, timeout=10,
                   target_temperature=30, number_of_trials=1, protocol=None, demo_mode=False):
        """This method is responsible for initialization of the device.
        """
        try:
            Autosampler.headers = column_headers
            self._demo_mode = demo_mode
            self._location = connection_port
            self._baudrate = baudrate
            # self._timeout = timeout
            self._connection = serial.Serial(connection_port, baudrate=baudrate)
            self._content = protocol
            # get_logger().info("protoocl: {}".format(self._content))
            self._number_of_trials = number_of_trials
            get_logger().info("Setting parameters to Autosampler connected at port {}.".format(connection_port))
            # self.calibration()
            self._protocolList = []
            Autosampler.state_buffer_lock.acquire()
            self._run_thread = threading.Thread(target=self._start_collection)
            self._run_thread.daemon = True
            self._read_protocol()
            get_logger().info("Successfully connected to Autosampler at port {}.".format(connection_port))
            return True
        except Exception as e:
            get_logger().warning(
                "Failed to create device connected to port {} due to :\n {}".format(connection_port, e))
            return False

    def calibration(self):
        """""
        List of commands that need to executed at the start of sampler
        """""
        try:
            time.sleep(2)
            start_time = datetime.now()
            self.command("G21\r\n")  # millimeters
            self.command("G90\r\n")  # Absolute Mode
            self.command("M302 S0\r\n")  # Disable cold extrusion
            self.command("G0 F" + str(Autosampler.feedrate) + "\r\n")  # Set speed

            self.command(
                "M92 X" + str(Autosampler.x_steps_per_unit) + " Y" + str(Autosampler.y_steps_per_unit) + " Z" + str(
                    Autosampler.z_steps_per_unit) + " E" + str(Autosampler.e_steps_per_unit) + "\r\n")  # Set steps/mm
            self.command("M201 X" + str(Autosampler.x_accel) + " Y" + str(Autosampler.y_accel) + " Z" + str(
                Autosampler.z_accel) + "\r\n")  # Max accel units/sec/sec
            self.command(
                "M203 X" + str(Autosampler.x_max_feedrate) + " Y" + str(Autosampler.y_max_feedrate) + " Z" + str(
                    Autosampler.z_max_feedrate) + " E" + str(
                    Autosampler.e_max_feedrate) + "\r\n")  # Max feedrate units/sec
            self.command("M204 P" + str(Autosampler.e_accel) + " R" + str(Autosampler.e_accel) + " S" + str(
                Autosampler.e_accel) + " T" + str(Autosampler.e_accel) + "\r\n")  # Max accel extruder units/sec/sec
            self.command("G92 X" + str(Autosampler.x_min) + " Y" + str(Autosampler.y_min) + " Z" + str(
                Autosampler.z_min) + " E" + str(Autosampler.e_min) + "\r\n")  # Set start position

            end_time = datetime.now()

            get_logger().info("Calibrated the Autosampler finished at {}".format(str(end_time - start_time)))
        except Exception as e:
            get_logger().info("Unable to calibrate the Autosampler")

    def command(self, command):

        messenger = self._connection
        messenger.write(str.encode(command))
        time.sleep(1)
        while True:
            line = messenger.readline()
            #            print(line)
            if line == b'ok\n':
                break

    def _read_protocol(self):
        # self._protocol_data_buffer_lock.
        if not Autosampler.PROTOCOL:
            get_logger().info("reading protocol")
            content = self._content
            number_of_trials = self._number_of_trials
            autoSampler_library_commands = {}
            # Trial_state = {}
            execution_time = 0
            for trial_id in range(number_of_trials):
                for trial_stage, stage_params in content.items():
                    trial_execution_length = stage_params['seconds']
                    stability_required = stage_params['stability_required']

                    for index, instruction in stage_params.items():
                        if 'command' in index:
                            autoSampler_library_commands[execution_time] = (
                                (instruction, trial_stage, trial_id + 1, trial_execution_length))
                            # get_logger().info("autoSampler_library_command: {}".format(autoSampler_library_commands))
                    execution_time += trial_execution_length
                Autosampler.PROTOCOL = autoSampler_library_commands
                # Autosampler.TRIAL_STATE = Trial_state
            get_logger().info(
                "Read AutoSampler protocol {}.".format(Autosampler.PROTOCOL))
            # get_logger().info(
            #     "Read MFC TRIAL_STATE {}.".format(Autosampler.TRIAL_STATE))

        autoSampler_library_commands = copy.deepcopy(Autosampler.PROTOCOL)
        # Trial_state = copy.deepcopy(Autosampler.TRIAL_STATE)
        try:
            for execution_time, command in (autoSampler_library_commands.items()):
                instruction, trial_stage, trial_id, trial_execution_length = command

                s = threading.Timer(execution_time, self._set_protocol,
                                    [instruction, trial_stage])
                self._protocolList.append(s)
                s.start()
                # get_logger().info(
                #     "Executing function {} from flow 0 to {} with {} seconds delay for {}.".format(
                #         self._set_protocol,
                #         set_flow, exec_time, mfc_state_and_stability))


        except Exception as e:
            '''Starting the reading thread can occur afterwards'''
        # time.sleep(5)
        if Autosampler.state_buffer_lock.locked():
            Autosampler.state_buffer_lock.release()
        time.sleep(1)
        self._run_thread.start()

    def _set_protocol(self, instruction, status):

        pick_up_location = (825,-350)
        min_height_with_holder = (650, 80)
        min_height_without_holder = (650, 120)
        transition_height = 275
        position_11 = (500, 350)
        position_12 = (400, 350)
        position_13 = (300, 350)
        position_14 = (215, 350)
        position_21 = (0, 350)
        position_22 = (0, 350)
        position_23 = (0, 350)
        position_24 = (0, 350)
        position_31 = (0, 350)
        position_32 = (0, 350)
        position_33 = (0, 350)
        position_34 = (0, 350)

        if instruction == "Baseline":
            start_time = datetime.now()
            pick_up_location_x, pick_up_location_z = pick_up_location

            self.command("G0 X" + str(pick_up_location_x) + "\r\n")  # Move
            self.command("G0 Z" + str(pick_up_location_z) + "\r\n")  # Move
            self.command("M400\r\n")  # Move
            end_time = datetime.now()
            get_logger().info("finished {} in {}".format(instruction, str(end_time - start_time)))
            self.setSampler_Status(status)

        if instruction == "Baseline_1":
            start_time = datetime.now()
            min_height_with_holder_x, min_height_with_holder_z = min_height_with_holder

            print("Baseline_1")
            self.command("M106 P0" + "\r\n")  # Move
            self.command(
                "G0 X{} Z{}".format(str(min_height_with_holder_x), str(min_height_with_holder_z)) + "\r\n")  # Move
            self.command("M400\r\n")  # Move
            self.setSampler_Status(status)
            end_time = datetime.now()
            print(end_time - start_time)
            print("done Baseline_1")

        if instruction == "Exposure_11":
            start_time = datetime.now()
            position_x, position_z = position_11
            min_height_without_holder_x, min_height_without_holder_z = min_height_without_holder

            self.setSampler_Status(status)
            self.command("G0 Y" + str(Autosampler.y_travel) + "\r\n")  # Move
            self.command("G0 X" + str(position_x) + "\r\n")  # Move
            self.command("G0 Z" + str(position_z) + "\r\n")  # Move
            self.command("M107 P0" + "\r\n")  # Move
            self.setSampler_Status(status)
            self.command("G0 Z" + str(min_height_without_holder_z) + "\r\n")  # Move
            self.command("G0 X" + str(min_height_without_holder_x) + "\r\n")  # Move
            self.command("G0 Y" + str(Autosampler.y_min) + "\r\n")  # Move
            self.command("M400\r\n")  # Move
            end_time = datetime.now()
            get_logger().info("finished {} in {}".format(instruction, str(end_time - start_time)))

        if instruction == "Exposure_12":
            start_time = datetime.now()
            position_x, position_z = position_12
            min_height_without_holder_x, min_height_without_holder_z = min_height_without_holder

            self.setSampler_Status(status)
            self.command("G0 Y" + str(Autosampler.y_travel) + "\r\n")  # Move
            self.command("G0 X" + str(position_x) + "\r\n")  # Move
            self.command("G0 Z" + str(position_z) + "\r\n")  # Move
            self.command("M107 P0" + "\r\n")  # Move
            self.setSampler_Status(status)
            self.command("G0 Z" + str(min_height_without_holder_z) + "\r\n")  # Move
            self.command("G0 X" + str(min_height_without_holder_x) + "\r\n")  # Move
            self.command("G0 Y" + str(Autosampler.y_min) + "\r\n")  # Move
            self.command("M400\r\n")  # Move
            end_time = datetime.now()
            get_logger().info("finished {} in {}".format(instruction, str(end_time - start_time)))

        if instruction == "Exposure_13":
            start_time = datetime.now()
            self.setSampler_Status(status)
            position_x, position_z = position_13
            min_height_without_holder_x, min_height_without_holder_z = min_height_without_holder

            self.command("G0 Y" + str(Autosampler.y_travel) + "\r\n")  # Move
            self.command("G0 X" + str(position_x) + "\r\n")  # Move
            self.command("G0 Z" + str(position_z) + "\r\n")  # Move
            self.command("M107 P0" + "\r\n")  # Move
            self.setSampler_Status(status)
            self.command("G0 Z" + str(min_height_without_holder_z) + "\r\n")  # Move
            self.command("G0 X" + str(min_height_without_holder_x) + "\r\n")  # Move
            self.command("G0 Y" + str(Autosampler.y_min) + "\r\n")  # Move
            self.command("M400\r\n")  # Move
            end_time = datetime.now()
            get_logger().info("finished {} in {}".format(instruction, str(end_time - start_time)))

        if instruction == "Exposure_14":
            start_time = datetime.now()
            self.setSampler_Status(status)
            position_x, position_z = position_14
            min_height_without_holder_x, min_height_without_holder_z = min_height_without_holder

            self.command("G0 Y" + str(Autosampler.y_travel) + "\r\n")  # Move
            self.command("G0 X" + str(position_x) + "\r\n")  # Move
            self.command("G0 Z" + str(position_z) + "\r\n")  # Move
            self.command("M107 P0" + "\r\n")  # Move
            self.setSampler_Status(status)
            self.command("G0 Z" + str(min_height_without_holder_z) + "\r\n")  # Move
            self.command("G0 X" + str(min_height_without_holder_x) + "\r\n")  # Move
            self.command("G0 Y" + str(Autosampler.y_min) + "\r\n")  # Move
            self.command("M400\r\n")  # Move
            end_time = datetime.now()
            get_logger().info("finished {} in {}".format(instruction, str(end_time - start_time)))

        if instruction == "Recovery_11":
            start_time = datetime.now()
            position_x, position_z = position_11
            min_height_with_holder_x, min_height_with_holder_z = min_height_with_holder
            pick_up_location_x, pick_up_location_z = pick_up_location

            self.command("G0 Y" + str(Autosampler.y_min + Autosampler.y_travel) + "\r\n")  # Move
            self.command("G0 X" + str(position_x) + "\r\n")  # Move
            self.command("G0 Z" + str(position_z) + "\r\n")  # Move
            self.command("M106 P0" + "\r\n")  # Move
            self.command("G0 Z" + str(min_height_with_holder_z) + "\r\n")  # Move
            self.command("G0 X" + str(min_height_with_holder_x) + "\r\n")  # Move
            self.command("G0 Y" + str(Autosampler.y_min) + "\r\n")  # Move
            self.setSampler_Status(status)
            self.command("G0 X{} Z{}".format(str(pick_up_location_x), str(pick_up_location_z)) + "\r\n")  # Move
            self.command("M107 P0" + "\r\n")  # Move
            self.command("G0 Z{}".format(Autosampler.z_min) + "\r\n")  # Move
            self.command("G0 X{}".format(Autosampler.x_min) + "\r\n")  # Move
            self.command("M400\r\n")  # Move
            end_time = datetime.now()
            get_logger().info("finished {} in {}".format(instruction, str(end_time - start_time)))

        if instruction == "Recovery_12":
            start_time = datetime.now()
            position_x, position_z = position_12
            min_height_with_holder_x, min_height_with_holder_z = min_height_with_holder
            pick_up_location_x, pick_up_location_z = pick_up_location

            self.command("G0 Y" + str(Autosampler.y_min + Autosampler.y_travel) + "\r\n")  # Move
            self.command("G0 X" + str(position_x) + "\r\n")  # Move
            self.command("G0 Z" + str(position_z) + "\r\n")  # Move
            self.command("M106 P0" + "\r\n")  # Move
            self.command("G0 Z" + str(min_height_with_holder_z) + "\r\n")  # Move
            self.command("G0 X" + str(min_height_with_holder_x) + "\r\n")  # Move
            self.command("G0 Y" + str(Autosampler.y_min) + "\r\n")  # Move
            self.setSampler_Status(status)
            self.command("G0 X{} Z{}".format(str(pick_up_location_x), str(pick_up_location_z)) + "\r\n")  # Move
            self.command("M107 P0" + "\r\n")  # Move
            self.command("G0 Z{}".format(Autosampler.z_min) + "\r\n")  # Move
            self.command("G0 X{}".format(Autosampler.x_min) + "\r\n")  # Move
            self.command("M400\r\n")  # Move
            end_time = datetime.now()
            get_logger().info("finished {} in {}".format(instruction, str(end_time - start_time)))

        if instruction == "Recovery_13":
            start_time = datetime.now()
            position_x, position_z = position_13
            min_height_with_holder_x, min_height_with_holder_z = min_height_with_holder
            pick_up_location_x, pick_up_location_z = pick_up_location

            self.command("G0 Y" + str(Autosampler.y_min + Autosampler.y_travel) + "\r\n")  # Move
            self.command("G0 X" + str(position_x) + "\r\n")  # Move
            self.command("G0 Z" + str(position_z) + "\r\n")  # Move
            self.command("M106 P0" + "\r\n")  # Move
            self.command("G0 Z" + str(min_height_with_holder_z) + "\r\n")  # Move
            self.command("G0 X" + str(min_height_with_holder_x) + "\r\n")  # Move
            self.command("G0 Y" + str(Autosampler.y_min) + "\r\n")  # Move
            self.setSampler_Status(status)
            self.command("G0 X{} Z{}".format(str(pick_up_location_x), str(pick_up_location_z)) + "\r\n")  # Move
            self.command("M107 P0" + "\r\n")  # Move
            self.command("G0 Z{}".format(Autosampler.z_min) + "\r\n")  # Move
            self.command("G0 X{}".format(Autosampler.x_min) + "\r\n")  # Move
            self.command("M400\r\n")  # Move
            end_time = datetime.now()
            get_logger().info("finished {} in {}".format(instruction, str(end_time - start_time)))

        if instruction == "Recovery_14":
            start_time = datetime.now()
            position_x, position_z = position_14
            min_height_with_holder_x, min_height_with_holder_z = min_height_with_holder
            pick_up_location_x, pick_up_location_z = pick_up_location

            self.command("G0 Y" + str(Autosampler.y_min + Autosampler.y_travel) + "\r\n")  # Move
            self.command("G0 X" + str(position_x) + "\r\n")  # Move
            self.command("G0 Z" + str(position_z) + "\r\n")  # Move
            self.command("M106 P0" + "\r\n")  # Move
            self.command("G0 Z" + str(min_height_with_holder_z) + "\r\n")  # Move
            self.command("G0 X" + str(min_height_with_holder_x) + "\r\n")  # Move
            self.command("G0 Y" + str(Autosampler.y_min) + "\r\n")  # Move
            self.setSampler_Status(status)
            self.command("G0 X{} Z{}".format(str(pick_up_location_x), str(pick_up_location_z)) + "\r\n")  # Move
            self.command("M107 P0" + "\r\n")  # Move
            self.command("G0 Z{}".format(Autosampler.z_min) + "\r\n")  # Move
            self.command("G0 X{}".format(Autosampler.x_min) + "\r\n")  # Move
            self.command("M400\r\n")  # Move
            end_time = datetime.now()
            get_logger().info("finished {} in {}".format(instruction, str(end_time - start_time)))

        if instruction == "Vacant_12_11":
            start_time = datetime.now()
            position_x1, position_z1 = position_12
            position_x2, position_z2 = position_11
            min_height_without_holder_x, min_height_without_holder_z = min_height_without_holder

            self.command("G0 Y" + str(Autosampler.y_min + Autosampler.y_travel) + "\r\n")  # Move
            self.command("G0 X" + str(position_x1) + "\r\n")  # Move
            self.command("G0 Z" + str(position_z1) + "\r\n")  # Move
            self.command("M106 P0" + "\r\n")  # Move
            self.command("G0 Z" + str(transition_height) + "\r\n")  # Move
            self.command("G0 X" + str(position_x2) + "\r\n")  # Move
            self.command("G0 Z" + str(position_z2) + "\r\n")  # Move
            self.command("M107 P0" + "\r\n")  # Move
            self.command("G0 Z" + str(min_height_without_holder_z) + "\r\n")  # Move
            self.command("G0 X" + str(min_height_without_holder_x) + "\r\n")  # Move
            self.command("G0 Y" + str(Autosampler.y_min) + "\r\n")  # Move
            self.setSampler_Status(status)
            self.command("M400\r\n")  # Move
            end_time = datetime.now()
            get_logger().info("finished {} in {}".format(instruction, str(end_time - start_time)))

        if instruction == "Vacant_13_12":
            start_time = datetime.now()
            position_x1, position_z1 = position_13
            position_x2, position_z2 = position_12
            min_height_without_holder_x, min_height_without_holder_z = min_height_without_holder

            self.command("G0 Y" + str(Autosampler.y_min + Autosampler.y_travel) + "\r\n")  # Move
            self.command("G0 X" + str(position_x1) + "\r\n")  # Move
            self.command("G0 Z" + str(position_z1) + "\r\n")  # Move
            self.command("M106 P0" + "\r\n")  # Move
            self.command("G0 Z" + str(transition_height) + "\r\n")  # Move
            self.command("G0 X" + str(position_x2) + "\r\n")  # Move
            self.command("G0 Z" + str(position_z2) + "\r\n")  # Move
            self.command("M107 P0" + "\r\n")  # Move
            self.command("G0 Z" + str(min_height_without_holder_z) + "\r\n")  # Move
            self.command("G0 X" + str(min_height_without_holder_x) + "\r\n")  # Move
            self.command("G0 Y" + str(Autosampler.y_min) + "\r\n")  # Move
            self.setSampler_Status(status)
            self.command("M400\r\n")  # Move
            end_time = datetime.now()
            get_logger().info("finished {} in {}".format(instruction, str(end_time - start_time)))

        if instruction == "Vacant_14_13":
            start_time = datetime.now()
            position_x1, position_z1 = position_14
            position_x2, position_z2 = position_13
            min_height_without_holder_x, min_height_without_holder_z = min_height_without_holder

            self.command("G0 Y" + str(Autosampler.y_min + Autosampler.y_travel) + "\r\n")  # Move
            self.command("G0 X" + str(position_x1) + "\r\n")  # Move
            self.command("G0 Z" + str(position_z1) + "\r\n")  # Move
            self.command("M106 P0" + "\r\n")  # Move
            self.command("G0 Z" + str(transition_height) + "\r\n")  # Move
            self.command("G0 X" + str(position_x2) + "\r\n")  # Move
            self.command("G0 Z" + str(position_z2) + "\r\n")  # Move
            self.command("M107 P0" + "\r\n")  # Move
            self.command("G0 Z" + str(min_height_without_holder_z) + "\r\n")  # Move
            self.command("G0 X" + str(min_height_without_holder_x) + "\r\n")  # Move
            self.command("G0 Y" + str(Autosampler.y_min) + "\r\n")  # Move
            self.setSampler_Status(status)
            self.command("M400\r\n")  # Move
            end_time = datetime.now()
            get_logger().info("finished {} in {}".format(instruction, str(end_time - start_time)))

        if instruction == "Vacant_11_14":
            start_time = datetime.now()
            position_x1, position_z1 = position_11
            position_x2, position_z2 = position_14
            min_height_without_holder_x, min_height_without_holder_z = min_height_without_holder

            self.command("G0 Y" + str(Autosampler.y_min + Autosampler.y_travel) + "\r\n")  # Move
            self.command("G0 X" + str(position_x1) + "\r\n")  # Move
            self.command("G0 Z" + str(position_z1) + "\r\n")  # Move
            self.command("M106 P0" + "\r\n")  # Move
            self.command("G0 Z" + str(transition_height) + "\r\n")  # Move
            self.command("G0 X" + str(position_x2) + "\r\n")  # Move
            self.command("G0 Z" + str(position_z2) + "\r\n")  # Move
            self.command("M107 P0" + "\r\n")  # Move
            self.command("G0 Z" + str(min_height_without_holder_z) + "\r\n")  # Move
            self.command("G0 X" + str(min_height_without_holder_x) + "\r\n")  # Move
            self.command("G0 Y" + str(Autosampler.y_min) + "\r\n")  # Move
            self.setSampler_Status(status)
            self.command("M400\r\n")  # Move
            end_time = datetime.now()
            get_logger().info("finished {} in {}".format(instruction, str(end_time - start_time)))

    def _start_collection(self):
        """This method is responsible for beginning collection.
        """
        self._status = Status.RUNNING
        while (self._status == Status.RUNNING):
            try:
                x = str(Autosampler.SAMPLER_STATE)
                # get_logger().info("X = {}".format(x))
                self.add_value(x)
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
        return Autosampler.headers

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
        for s in self._protocolList:
            s.cancel()
        get_logger().info("Closing the Autosampler sensor connected to {}".format(self._connection.port))
        self._connection.close()
        self._status = Status.TERMINATED

    def add_value(self, value):
        self._last20.append(value)
        del self._last20[0]

    def setSampler_Status(self, status):
        # Autosampler.state_buffer_lock.acquire()

        # if Autosampler.state_buffer_lock.locked():
        Autosampler.SAMPLER_STATE = status

        # Autosampler.state_buffer_lock.release()

    def getSampler_Status(self):
        current_status = Autosampler.SAMPLER_STATE
        return current_status
