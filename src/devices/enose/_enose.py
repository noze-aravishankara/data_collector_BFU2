
import os
import serial
import struct
import sys
import time
import threading


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from devices.enose._link import synchronized, DataLink
from utility.time_utils import get_unix_timestamp
from devices.base_device import ABCDevice


POLYMER_COUNT = 31
BYTE_READER_CHAR = "<" if sys.byteorder == "little" else ">"
VALID_DATA_LENGTH = (POLYMER_COUNT+5)*4
ADDITIONAL_DATA = [("UnixTS", get_unix_timestamp)]

_PAYLOAD_STRUCTURE = [("TimeStamp", [0,4], BYTE_READER_CHAR+"I")] + \
                     [("PrecisionResistor", [4,8], BYTE_READER_CHAR+"I")] + \
                     [("Sensor{}".format(i), [(i+2)*4,(i+3)*4], BYTE_READER_CHAR+"I") for i in range(POLYMER_COUNT)] + \
                     [("Temperature", [(POLYMER_COUNT+2)*4,(POLYMER_COUNT+3)*4], BYTE_READER_CHAR+"f")] + \
                     [("TargetTemperature", [(POLYMER_COUNT+3)*4,(POLYMER_COUNT+4)*4], BYTE_READER_CHAR+"f")] + \
                     [("ControlVariable", [(POLYMER_COUNT+4)*4,(POLYMER_COUNT+5)*4], BYTE_READER_CHAR+"f")]
_PAYLOAD_LENGTH = len(_PAYLOAD_STRUCTURE)



class ENose(ABCDevice):
    """

    """
    name = "enose"
    def __init__(self, connection_port=None, baudrate=115200, timeout=2, target_temperature=25):
        """

        :param connection:

        Todo:
            * _target_temperature should be a property.
        """
        self._connection = self._initialize_serial_port(connection_port, baudrate, timeout)
        self._measurement_powered_on = False
        self._measurement_started = False
        self._link = None
        self.lock = threading.RLock()
        self._data = []
        self._events = {}
        self._frames = {}
        self._target_temperature = target_temperature
        self._read_data = True
        ABCDevice.__init__(self)

    def _initialize_serial_port(self, connection_port, baudrate=115200, timeout=2):
        return serial.Serial(connection_port, baudrate=baudrate, timeout=timeout)

    @synchronized('lock')
    def _buffer_data(self, data=None):
        """
        Parse an encoded data frame and store it in the buffer.

        :param data: (string)
        :return: None
        """
        n = len(data)
        if n != VALID_DATA_LENGTH:
            raise IOError("Invalid data length.")
        frame = [None]*(_PAYLOAD_LENGTH+len(ADDITIONAL_DATA))
        for idx,item in enumerate(_PAYLOAD_STRUCTURE):
            frame[idx] = struct.unpack(item[2], data[item[1][0]:item[1][1]])[0]
        for idx in range(len(ADDITIONAL_DATA)):
            frame[_PAYLOAD_LENGTH+idx] = ADDITIONAL_DATA[idx][1]()
        self._data.append(frame)

    def _callback(self, opcode=None, payload=None):
        """
        Handle the contents of a received frame.

        (This function executes on the daemon thread.)

        :param opcode:
        :param payload:
        :return: None
        """
        if opcode == 0xff:
            self._buffer_data(data=payload)
        else:
            self._frames[opcode] = payload
            self._get_event(opcode=opcode).set()

    def _command(self, opcode=None, payload=None, timeout=5.0):
        """

        :param opcode:
        :param payload:
        :param timeout:
        :return:
        """
        # Clear event flag
        event = self._get_event(opcode=opcode)
        event.clear()
        # Response will be processed on daemon thread - wait until event is set
        self._link.write(opcode=opcode, payload=payload)
        if event.wait(timeout=timeout):
            if event.is_set():
                return self._frames[opcode]
            else:
                return None
        else:
            # Occurs on event timeout
            raise IOError("Timed out while awaiting response from device.")

    def _get_event(self, opcode):
        """
        Retrieve the event (threading.Event) associated with the specified opcode.

        :param opcode:
        :return: (threading.Event)
        """
        try:
            event = self._events[opcode]
        except KeyError as e:
            event = threading.Event()
            self._events[opcode] = event
        return event

    def _loop(self, wait=0.1):
        """
        Process incoming data over the link. This function does not return.

        (This function executes on the daemon thread.)

        :param wait:
        :return: None
        """
        while self._read_data:
            self._link.read_all()
            time.sleep(wait)

    def get_required_arguments_to_build(self):
        """
        """
        return {"connection": None, "baudrate": 115200, "timeout": 2}

    def initialize(self):
        """

        """
        self.connect()
        self._initialized = True
        self.set_target_temperature(self._target_temperature)
        self.measurement_power_on()

    @synchronized('lock')
    def connect(self):
        """
        Establish the link layer connection with the device. This function starts the daemon thread.

        :return: None
        """
        self._link = DataLink(connection=self._connection, callback=self._callback)
        self._worker = threading.Thread(target=self._loop)
        self._worker.daemon = True
        self._worker.start()

    @synchronized('lock')
    def echo(self, argument=''):
        """
        Execute the "Echo" command (0x20).

        :param argument: (string)
        :return: (string)
        """
        result = self._command(opcode=0x20, payload=argument)
        return result

    @synchronized('lock')
    def enter_bootloader(self, argument=''):
        """
        Execute the "Enter Bootloader" command (0x21).

        Note: This will switch to the Cypress Bootloader protocol. Refer to Cypress document no. 002-09794,
        "Bootloader and Bootloadable" for more details.

        :param argument: (string)
        :return: (string)
        """
        result = self._command(opcode=0x21, payload=argument)
        return result

    @synchronized('lock')
    def flash_device_id(self, device_type=None, location=None, batch=None, serial_number=None):
        """
        Execute the "Flash Device ID" command (0x28).

        :param device_type: (uint8)
        :param location: (uint8)
        :param batch: (uint16)
        :param serial_number: (uint32)
        :return: (string)
        """
        payload = struct.pack('>BBHI', device_type, location, batch, serial_number)
        result = self._command(opcode=0x28, payload=payload)
        return result

    @synchronized('lock')
    def flash_hardware_version(self, major=None, minor=None, revision=None):
        """
        Execute the "Flash Hardware Version" command (0x29).

        :param major: (uint8)
        :param minor: (uint8)
        :param revision: (uint8)
        :return: (string)
        """
        payload = struct.pack('BBBB', major, minor, revision, 0)
        result = self._command(opcode=0x29, payload=payload)
        return result

    @synchronized('lock')
    def get_data(self, flush=True):
        """
        Get the data currently held in the buffer.

        :param flush: (bool)
        :return: (list)
        """
        if not self._measurement_started:
            self.measurement_start()
        data = list(self._data)
        if flush:
            self._data = []
        return data

    @synchronized('lock')
    def get_header(self):
        """
        Execute the "Get Header" command (0x48).

        :return: (tuple)
        """
        if not self._initialized:
            self.initialize()
        result = self._command(opcode=0x48, payload='')
        device_id = result[0:8].encode('hex')
        hardware_version = struct.unpack('BBBB', result[8:12])
        firmware_version = struct.unpack('BBBB', result[12:16])
        return [device_id, hardware_version, firmware_version]

    @synchronized('lock')
    def measurement_power_off(self):
        """
        Execute the "Measurement Power Off" command (0x60).

        :return: (string)
        """
        result = self._command(opcode=0x60, payload='')
        self._measurement_powered_on = False
        self._measurement_started = False
        return result

    @synchronized('lock')
    def measurement_power_on(self):
        """
        Execute the "Measurement Power On" command (0x61).

        :return: (string)
        """
        self._measurement_powered_on = True
        result = self._command(opcode=0x61, payload='')
        return result

    @synchronized('lock')
    def measurement_start(self):
        """
        Execute the "Measurement Start" command (0x62).

        :return: (string)
        """
        if not self._initialized:
            self.initialize()
        if not self._measurement_powered_on:
            self.measurement_power_on()
        result = self._command(opcode=0x62, payload='')
        self._measurement_started = True
        return result

    @synchronized('lock')
    def measurement_stop(self):
        """
        Execute the "Measurement Stop" command (0x63).

        :return: (string)
        """
        result = self._command(opcode=0x63, payload='')
        self._measurement_started = False
        return result

    @synchronized('lock')
    def set_target_temperature(self, temperature=None):
        """
        Execute the "Set Target Temperature" command (0x52).

        :param temperature: (float)
        :return: (string)
        """
        self._target_temperature = temperature
        result = self._command(opcode=0x52, payload=struct.pack('<f', temperature))
        return result

    @staticmethod
    def get_data_info():
        """
        Returns the column names related to the data received by this module.

        :returns: List[string]
        """
        data_info = [p[0] for p in _PAYLOAD_STRUCTURE]
        data_info.extend([ad[0] for ad in ADDITIONAL_DATA])
        return data_info

    def terminate(self):
        self.measurement_stop()
        self.measurement_power_off()
        self._read_data = False
        self._data = []
        self._connection.close()
