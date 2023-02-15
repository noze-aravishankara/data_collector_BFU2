# import logging
import copy
import logging
import traceback
from enum import Enum
import os
import sensirion_shdlc_driver.port
import serial
import threading
import time
import sys
import time
import numpy as np
import serial
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from sensirion_shdlc_driver.errors import ShdlcDeviceError
from serial.tools import list_ports

from utility.logger import get_logger
from utility.time_utils import get_unix_timestamp
from MFC.base_MFC import ABCMFC
from threading import Timer
import configparser

from sensirion_shdlc_driver import ShdlcSerialPort, ShdlcConnection
from sensirion_shdlc_sfc5xxx import Sfc5xxxShdlcDevice, Sfc5xxxScaling, Sfc5xxxValveInputSource, Sfc5xxxUnitPrefix, \
    Sfc5xxxUnit, Sfc5xxxUnitTimeBase, Sfc5xxxMediumUnit

sensirion_shdlc_driver.port.log.setLevel(level=logging.CRITICAL)

_BUFFER_SIZE = 20

_ZERO_THRESHOLD = 0.25
_SETPOINT_THRESHOLD = 0.075

_UNIT = Sfc5xxxMediumUnit(
    Sfc5xxxUnitPrefix.MILLI,
    Sfc5xxxUnit.STANDARD_LITER,
    Sfc5xxxUnitTimeBase.MINUTE
)


class Status(Enum):
    UNINITIALIZED = 0
    RUNNING = 2
    PAUSED = 3
    STOPPED = 4
    TERMINATED = 5
    DISCONNECTED = 6


class ProgramCompleted(BaseException):
    pass


class MFCUnableToStart(BaseException):
    pass


class Sensirion_SFC500(ABCMFC):
    """
    """
    name = "sensirion_sfc500"
    _mfcStatusBuffer = [""] * _BUFFER_SIZE
    MFC_STATE = "baseline"
    MFC_STATE_EXEC_LENGTH = 0
    TRIAL_ID = 1
    PROTOCOL = {}
    TRIAL_STATE = {}
    TRIGGER_REQUIRED = False
    MFC_ACTIVE = False  # Class Variable to indicate whether there are any MFCs instances that have self._enabled to be true
    state_buffer_lock = threading.Lock()
    instances = []

    def __init__(self):
        Sensirion_SFC500.__instance = self
        self.__class__.instances.append(self)
        self._status = Status.UNINITIALIZED
        self._last20 = [""] * _BUFFER_SIZE
        self._protocol_data_buffer_lock = threading.Lock()

    # self._data_buffer = []

    # @abc.abstractmethod
    def initialize(self, connection_port, column_headers=["mfc"], analyte=None, enabled=False, report_label=False,
                   ground_truth=True, number_of_trials=1, protocol=None,
                   baudrate=115200, serial_number=0000000,
                   timeout=10, slave_address=0):
        """This method is responsible for initialization of the MFC.
        """
        try:
            self._name = column_headers[0].upper()
            self._reportlabel = report_label
            self._groundtruth = ground_truth
            self._headers = column_headers
            self._analyte = analyte
            self._serial_ID = serial_number
            self._run_thread = threading.Thread(target=self._start_collection)
            self._run_thread.daemon = True
            self._enabled = enabled
            self._number_of_trials = number_of_trials
            self._content = protocol
            self._protocolList = []
            # self._trigger_required = False
            # self._read_protocol()
            if not self._reportlabel:
                self._headers = [column_headers[0]]
            if self._enabled:
                Sensirion_SFC500.MFC_ACTIVE = True
                _mfc = Sfc5xxxShdlcDevice(ShdlcConnection(ShdlcSerialPort(connection_port, baudrate)), slave_address)
                _mfc.activate_calibration(0)
                _mfc.set_user_defined_medium_unit(_UNIT)
                _mfc.set_reply_delay(3)
                self._device = _mfc
                # self._serial_ID = _mfc.get_serial_number()
                self._location = connection_port
                self._baudrate = baudrate
                self._timeout = timeout
                # self._protocol_data_buffer_lock.acquire()
                # if self._protocol_data_buffer_lock.locked():
                get_logger().info(
                    "Successfully connected to MFC {} at port {}.".format(self._serial_ID, connection_port))
            # else:
            #     self._run_thread.start()

            Sensirion_SFC500.state_buffer_lock.acquire()
            self._read_protocol()
            return True
        except Exception as e:
            get_logger().warning(
                "Failed to create MFC device connected to port {} due to :\n {}".format(connection_port, e))
            return False

    '''NEEED A SETUP TO READ AND TRIGGER THE PROTOCOL, USE MFC_PROGRAM TO START THIS'''

    def _read_protocol(self):
        # self._protocol_data_buffer_lock.
        if not Sensirion_SFC500.PROTOCOL:

            content = self._content
            number_of_trials = self._number_of_trials
            MFC_library_commands = {}
            Trial_state = {}
            execution_time = 0
            for trial_id in range(number_of_trials):
                for trial_stage, stage_params in content.items():
                    trial_execution_length = stage_params['seconds']
                    stability_required = stage_params['stability_required']
                    if not MFC_library_commands:
                        MFC_library_commands = {key: [] for key in stage_params.keys() if 'MFC' in key}
                    for mfc_id, mfc_flow in stage_params.items():
                        if 'MFC' in mfc_id:
                            MFC_library_commands[mfc_id].append(
                                (execution_time, mfc_flow, trial_id + 1, trial_execution_length))

                    Trial_state[execution_time] = [trial_stage, stability_required]
                    execution_time += trial_execution_length
                Sensirion_SFC500.PROTOCOL = MFC_library_commands
                Sensirion_SFC500.TRIAL_STATE = Trial_state
            get_logger().info(
                "Read MFC protocol {}.".format(Sensirion_SFC500.PROTOCOL))
            get_logger().info(
                "Read MFC TRIAL_STATE {}.".format(Sensirion_SFC500.TRIAL_STATE))

        MFC_library_commands = copy.deepcopy(Sensirion_SFC500.PROTOCOL)
        Trial_state = copy.deepcopy(Sensirion_SFC500.TRIAL_STATE)
        try:
            for idx, command in enumerate(MFC_library_commands[self._name]):
                exec_time, set_flow, trial_id, trial_execution_length = command
                mfc_state_and_stability = Trial_state[exec_time]
                # get_logger().info(
                #     "exec_length:{} mfc_state:{} trial_id:{}".format(trial_execution_length, mfc_state_and_stability,
                #                                                      trial_id))

                if exec_time == 0:
                    s = threading.Timer(exec_time, self._set_protocol,
                                        [trial_execution_length, 0, set_flow, mfc_state_and_stability, trial_id])
                    self._protocolList.append(s)
                    s.start()
                    # get_logger().info(
                    #     "Executing function {} from flow 0 to {} with {} seconds delay for {}.".format(
                    #         self._set_protocol,
                    #         set_flow, exec_time, mfc_state_and_stability))

                else:
                    prev_exec_time, prev_set_flow, prev_trial_id, prev_trial_execution_length = \
                        MFC_library_commands[self._name][idx - 1] if idx > 0 else None

                    s = threading.Timer(exec_time, self._set_protocol,
                                        [trial_execution_length, prev_set_flow, set_flow, mfc_state_and_stability,
                                         trial_id])

                    self._protocolList.append(s)
                    s.start()
                    # get_logger().info(
                    #     "Executing function {} from flow {} to {} with {} seconds delay for {}.".format(
                    #         self._set_protocol,
                    #         prev_set_flow,
                    #         set_flow,
                    #         exec_time, mfc_state_and_stability))
        except Exception as e:
            '''Starting the reading thread can occur afterwards'''
        # time.sleep(5)
        if Sensirion_SFC500.state_buffer_lock.locked():
            Sensirion_SFC500.state_buffer_lock.release()
        time.sleep(1)
        self._run_thread.start()

        '''after parsing the Protocol file , it should be able to identify the right steps to excecute based on  instance's name;
            the seconds and the flow value,maybe packaged as a list or tuple as the return type
        '''

    def _set_protocol(self, state_execution_time, from_setpoint_flow, to_setpoint_flow, trial_state, trial_id):
        """This is similar function to Transition_Flow from original function
            it checks the flow from inital state to its next state and controls the steps it takes to get there.
        """
        Sensirion_SFC500.state_buffer_lock.acquire()

        if Sensirion_SFC500.state_buffer_lock.locked() and (self._groundtruth or not Sensirion_SFC500.MFC_ACTIVE):
            Sensirion_SFC500.MFC_STATE = str(trial_state[0])
            Sensirion_SFC500.TRIGGER_REQUIRED = trial_state[1]

            x = str(
                Sensirion_SFC500.MFC_STATE + "," + str(state_execution_time) + "," + str(
                    trial_id))
            self.update_status(x)

        Sensirion_SFC500.state_buffer_lock.release()
        self._trialState = str(trial_state[0])

        if self._enabled:
            if from_setpoint_flow == 0 and to_setpoint_flow > 0:
                if to_setpoint_flow <= 1:
                    setpoint = to_setpoint_flow
                else:
                    setpoint = 1
            else:
                setpoint = from_setpoint_flow

            self._set_mfc_value(setpoint)
            self._check_flow(setpoint)

            midpoint = int(to_setpoint_flow + from_setpoint_flow) / 2

            self._set_mfc_value(midpoint)
            self._check_flow(midpoint)

            self._set_mfc_value(to_setpoint_flow)
            self._check_flow(to_setpoint_flow)

        if Sensirion_SFC500.TRIAL_STATE:
            if self == Sensirion_SFC500.instances[-1] and len(Sensirion_SFC500.instances) \
                    == len(Sensirion_SFC500.PROTOCOL.keys()):
                # this condition ensures that it is the last instance that removes the trial_state
                exec_time, _, _, _ = Sensirion_SFC500.PROTOCOL[self._name][0]
                Sensirion_SFC500.TRIAL_STATE.pop(exec_time, None)
                # get_logger().info(
                #     "popped executed command and update MFC TRIAL_STATE {} from {}.".format(
                #         Sensirion_SFC500.TRIAL_STATE,
                #         self._name))
        if not Sensirion_SFC500.TRIAL_STATE:
            Sensirion_SFC500.TRIGGER_REQUIRED = False

        if Sensirion_SFC500.PROTOCOL[self._name]:
            Sensirion_SFC500.PROTOCOL[self._name].pop(0)
            # get_logger().info(
            #     "popped executed command and update MFC protocol {} from {}.".format(Sensirion_SFC500.PROTOCOL,
            #                                                                          self._name))
        else:
            get_logger().info(
                "no more commands left from {}.".format(Sensirion_SFC500.PROTOCOL,
                                                        self._name))

    def _update_protocol(self):
        """
        Function is only triggered if device_stability from simple_enose or chamber_simple_enose is called.
        Updates the current executed protocol to indicate that a change is required because signal stability is achieved.

        """
        Sensirion_SFC500.state_buffer_lock.acquire()
        MFC_library_commands = copy.deepcopy(self.PROTOCOL)
        Trial_state = copy.deepcopy(self.TRIAL_STATE)

        try:
            if self._groundtruth:
                new_execution_time = [*Trial_state.keys()]
                new_execution_time.sort()
                execution_time_reset_value = new_execution_time[0]
                new_execution_time = np.array(new_execution_time)
                new_execution_time = new_execution_time - execution_time_reset_value
                new_execution_time = new_execution_time.tolist()

                # get_logger().info("new execution time: {}".format(new_execution_time))
                # get_logger().info("old protocol: {}".format(Sensirion_SFC500.PROTOCOL))
                # get_logger().info("old MFC TRIAL_STATE: {}".format(Sensirion_SFC500.TRIAL_STATE))
                updated_trial_info = {}
                for trial_time, new_time in zip(Trial_state, new_execution_time):
                    updated_trial_info[new_time] = Trial_state[trial_time]

                Sensirion_SFC500.TRIAL_STATE = updated_trial_info
                # get_logger().info("updated MFC TRIAL_STATE: {}".format(Sensirion_SFC500.TRIAL_STATE))

            new_execution_time = [*Sensirion_SFC500.TRIAL_STATE.keys()]
            new_execution_time.sort()

            new_command_list = []
            for command, new_time in (zip(MFC_library_commands[self._name], new_execution_time)):

                exec_time, set_flow, trial_id, trial_execution_length = command
                updated_command = new_time, set_flow, trial_id, trial_execution_length
                new_command_list.append(updated_command)
                if Sensirion_SFC500.state_buffer_lock.locked():
                    Sensirion_SFC500.PROTOCOL[self._name] = new_command_list

            get_logger().info("updated protocol: {}".format(Sensirion_SFC500.PROTOCOL))

            if self._enabled:
                for s in self._protocolList:
                    s.cancel()
                self._protocolList = []

                get_logger().info("cancelled current pending action for {}".format(self._name))

                MFC_library_commands = copy.deepcopy(Sensirion_SFC500.PROTOCOL)
                Trial_state = Sensirion_SFC500.TRIAL_STATE

                try:
                    for idx, command in enumerate(MFC_library_commands[self._name]):
                        exec_time, set_flow, trial_id, trial_execution_length = command
                        mfc_state_and_stability = Trial_state[exec_time]
                        get_logger().info(
                            "exec_length:{} mfc_state:{} trial_id:{}".format(trial_execution_length,
                                                                             mfc_state_and_stability,
                                                                             trial_id))

                        if exec_time == 0:
                            prev_set_flow = self._get_mfc_value()
                            s = threading.Timer(exec_time, self._set_protocol,
                                                [trial_execution_length, prev_set_flow, set_flow,
                                                 mfc_state_and_stability, trial_id])
                            self._protocolList.append(s)
                            s.start()
                            get_logger().info(
                                "Executing function {} from flow {} to {} with {} seconds delay for {}.".format(
                                    self._set_protocol,
                                    prev_set_flow,
                                    set_flow,
                                    exec_time, mfc_state_and_stability))

                        else:
                            prev_exec_time, prev_set_flow, prev_trial_id, prev_trial_execution_length = \
                                MFC_library_commands[self._name][idx - 1] if idx > 0 else None

                            s = threading.Timer(exec_time, self._set_protocol,
                                                [trial_execution_length, prev_set_flow, set_flow,
                                                 mfc_state_and_stability,
                                                 trial_id])

                            self._protocolList.append(s)
                            s.start()
                            get_logger().info(
                                "Executing function {} from flow {} to {} with {} seconds delay for {}.".format(
                                    self._set_protocol,
                                    prev_set_flow,
                                    set_flow,
                                    exec_time, mfc_state_and_stability))
                except Exception as e:
                    get_logger().info(e)
                    get_logger().info("did not execute the newly set out protocol for {}".format(self._name))
            #     '''Starting the reading thread can occur afterwards'''
            # # time.sleep(5)

            if Sensirion_SFC500.state_buffer_lock.locked():
                Sensirion_SFC500.state_buffer_lock.release()
            # time.sleep(1)
        except:
            get_logger().info("unable to update protocol")

    def _set_mfc_value(self, set_value):

        mfc = self._device
        if not mfc.last_error_flag:
            try:
                mfc.set_setpoint(set_value, Sfc5xxxScaling.USER_DEFINED)
                get_logger().info(
                    '{} set to {} sccm with status :{}'.format(self._name, set_value, mfc.read_device_status()))

            except Exception as e:
                get_logger().critical(
                    'Due to error: \n {} \n {} cannot set to {} sccm'.format(e, self._name, set_value))
        else:
            for s in self._protocolList:
                s.cancel()
                get_logger().error('Due to error: \n cancelling {} '.format(s))
            get_logger().error('Due to error: {}\n cancelling {}  '.format(mfc.read_device_status(), self._name))

            raise ShdlcDeviceError

    def _get_mfc_value(self):

        mfc = self._device
        if not mfc.last_error_flag:
            try:
                val = self._device.read_measured_value(Sfc5xxxScaling.USER_DEFINED)
                return val
            except Exception as e:
                get_logger().critical('Due to error: \n {} \n {} cannot read '.format(e, self._name))
        else:
            for s in self._protocolList:
                s.cancel()
                get_logger().error('Due to error: \n cancelling {} '.format(s))
            get_logger().error('Due to error: {}\n cancelling {}  '.format(mfc.read_device_status(), self._name))
            raise ShdlcDeviceError

    def _check_flow(self, flow_value):
        flag = False
        while not flag:
            flag = True
            val = self._get_mfc_value()

            if flow_value == 0:
                if val <= _ZERO_THRESHOLD:
                    continue
            elif abs((val - flow_value) / flow_value) <= _SETPOINT_THRESHOLD:
                continue
            else:
                flag = False
            get_logger().info("Measured Values For Test: {}".format(str(val)))
            time.sleep(0.25)

    def _start_collection(self):
        """This method is responsible for beginning collection.
        """

        """
        it should read all of the protocols set by the protocol and schedule it for to start before the _STATUS is set
        to RUNNING.
        
        """
        self._status = Status.RUNNING
        while self._status == Status.RUNNING:
            try:
                if self._enabled:
                    # state = self._trialState
                    time.sleep(0.5)
                    x = self._get_mfc_value()
                else:
                    # state = self.MFC_STATE
                    x = str(-1.0)

                if self._reportlabel:
                    # if self._name == "MFC_5":
                    x = str(x) + "," + self.MFC_STATE
                    """
                    self._reportlabel only will report the label of the ground_truth MFCs or unless all MFCs are turned off
                    it will report as per protocol.                                        
                    """
                    # else:
                    #     x = str(x) + "," + state

                time.sleep(1)
                self.add_value(str(x))

                # get_logger().info("mfc_status: {}".format(str(Sensirion_SFC500.MFC_STATE + ',' + str(Sensirion_SFC500.MFC_STATE_EXEC_LENGTH) + ',' + str(
                #     Sensirion_SFC500.TRIAL_ID))))

                # get_logger().info("mfc_status_2: {}".format(self.get_status()))


            except:
                if self._reportlabel:
                    x = str(None) + "," + self.MFC_STATE
                    self.add_value(x)
                else:
                    self.add_value(str(None))
                get_logger().critical(
                    "MFC : {} at {} disconnected.Program will now terminate".format(
                        self._name, self._location))
                raise MFCUnableToStart

    def get_required_arguments_to_build(self):
        return {"connection": None, "baudrate": 115200, "timeout": 10}

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

        """
        return self._headers

    def get_data(self):
        """This method is responsible for fetching the data from the device and returning a list containing all the data received
            from the device and not been sent.

        """
        # get_logger().info("Adding {} of type {} to {}.".format(self._last20[-1], type(self._last20[-1]), self._name))

        return self._last20[-1]

    def get_status(self):
        """This method is responsible for fetching the data from the device referring to its status and returning a list containing all the data received
            from the device and not been sent.
        """
        state, exec_length, trial_id = self._mfcStatusBuffer[-1].split(",")
        self._mfcStatusBuffer[-1] = state + "," + (
            str(int(exec_length) - 1) if int(exec_length) - 1 > 0 else str(0)) + "," + trial_id

        if (not Sensirion_SFC500.TRIAL_STATE) and (self._groundtruth or not Sensirion_SFC500.MFC_ACTIVE) and int(
                exec_length) == 0:
            get_logger().info("Program terminating through an automatic KeyboardInterupt")
            raise ProgramCompleted

        return self._mfcStatusBuffer[-1]

    def get_trigger_required(self):

        required = Sensirion_SFC500.TRIGGER_REQUIRED
        return required

    def reset_mfc(self):
        if self._enabled:
            for s in self._protocolList:
                s.cancel()
            self._device.set_setpoint(0, Sfc5xxxScaling.USER_DEFINED)
            self._device.device_reset()

    def terminate(self):
        """This method is responsible for termination of the connection and also taking required measurements to dispose the device object..
        """
        if self._status != Status.TERMINATED:
            self._status = Status.STOPPED
            get_logger().info("Closing the Sensirion MFC named {}".format(self._name))
            self.reset_mfc()
            time.sleep(1)
            self._status = Status.TERMINATED
            """
            needs to be validated if all of the MFCs are still shutting down
            """
    def add_value(self, value):
        self._last20.append(value)
        del self._last20[0]

    def update_status(self, value):
        self._mfcStatusBuffer.append(value)
        del self._mfcStatusBuffer[0]
