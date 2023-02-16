#!/usr/bin/env python3

"""
Company     : NOZE
Author      : Eddy Fraga
Created on  : January 20, 2023
File type   : python
File name   : constants.py
Description : Python constants used for BFU MSP430 project.
Reference   : N/A
"""


class options:  # AVAILABLE OPTION ARGUMENTS
    ARG = '-'
    HELP = '-h'
    METADATA = '-m'
    TELEMETRY = '-t'
    CALIB = '-c'
    SHOW_NVM = '-n'
    UPDATE_NVM = '-u'
    CFIG_FILE_EXT = '.json'  # EXPECTED NVM BFU CONFIGURATION FILE EXTENSION


class portInfo:
    COMM_WIN = 'COM'
    COMM_LINUX = '/dev/tty'
    BFU_BAUDRATE = 115200


class compatibleOS:
    LINUX = 'Linux'
    WINDOWS = 'Windows'


class bfuCommand:  # BFU UART COMMANDS
    TELEMETRY_MSG_PRINTING = "pxxxx"
    OUPUT_NVM = "dxxxx"
    OUPUT_METADATA = "mxxxx"
    UPDATE_PAYLOAD_TIMER = 't'
    UPDATE_ADC_AVERAGING = 'a'
    UPDATE_MUX_DELAY = 'x'
    UPDATE_CHEMI_RES_OFFSET = "oxxxx"
    UPDATE_FAN_PWM = 'f'
    SN_NVM = 65  # 'A' character
    PROG_NVM = "n7171"
    SUCCESS_RESULT = "CMD SUCCESS!"


class nvmInfo:
    NVM_START_ADDRS = 49152
    NB_OF_NVM_PRINT_ROWS = 64   # 1024/16 = 64 rows of hex data


# TIMING CONSTANTS
class bfuTiming:
    SERIAL_TIMEOUT_DELAY_SEC = 10
    SERIAL_WAIT_DELAY_SEC = 0.01
    BFU_DELAY_BEFORE_CMD = 3


class endMsg:   # BFU END MESSAGE CHARACTERS
    END_PAYLOAD = bytes("\r\n\n", "ascii")
    END_NVM_LINE = bytes("\r", "ascii")


KEY_CHEMI_RES_CALIB = 'chemiResistorOffsetCorrection'
CALIB_CHEMI_RES_OFFSET = "CAL_OFFSET"


class jsonInfo:
    TELEMETRY_KEY = 't'  # BFU TELEMETRY JSON KEY

    # BFU JSON KEYS (STRINGS)
    AVAILABLE_NVM_META_STRINGS = ["serialNumber", "hv", "fv",
                                  "payloadVersion", "assembledBy", "assemblyVersion", "manufacturedAt"]

    # EXPECTED BFU JSON VALUES LENGTH (STRINGS)
    NVM_STRINGS_SIZE = [22, 11, 11, 3, 20, 3, 20]

    # BFU JSON KEYS (INTEGERS)
    AVAILABLE_NVM_INTEGERS = ["payloadTimerDelayInSeconds", "adcAveraging",
                              "muxDelayMultiplier", "fanPWM"]


class setupIndex:  # ARRAY SETUP INDEX
    COMM = 0
    CFIG = 1
    METADATA = 2
    CALIBRATE = 3
    TELEMETRY = 4
    SHOW_NVM = 5
    NB_OF_SETUP_ARG = (SHOW_NVM+1)
