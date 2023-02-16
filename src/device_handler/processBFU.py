#!/usr/bin/env python3

"""
Company     : NOZE
Author      : Eddy Fraga
Created on  : January 20, 2023
File type   : python
File name   : processBFU.py
Description : Python interface class allowing access to the MSP-BFU module.
Reference   : N/A
"""

import json
from time import sleep

from .constants import bfuCommand, nvmInfo, endMsg, bfuTiming, jsonInfo
from .serialComm import SerialComm


class processBfu:

    telemetry_msg_status = True
    status = True

    def __init__(self, comm_port):
        self.comm = SerialComm(comm_port)


    def get_port_status(self):
        return self.comm.get_status()

    def _build_metadata_cmd(self, cmd, idx, value):
        return cmd + str(idx).zfill(3) + value

    def disable_telemetry(self):
        if self.telemetry_msg_status is True:
            self.comm.write_data(bfuCommand.TELEMETRY_MSG_PRINTING)
            self.telemetry_msg_status = False
        sleep(bfuTiming.BFU_DELAY_BEFORE_CMD)
        self.comm.flush_all_input_data()

    def enable_telemetry(self):
        if self.telemetry_msg_status is False:
            self.comm.write_data(bfuCommand.TELEMETRY_MSG_PRINTING)
            self.telemetry_msg_status = True
        self.comm.flush_all_input_data()

    def calibrate_chemresistor_offset(self):
        return self.comm.write_data_with_response(bfuCommand.UPDATE_CHEMI_RES_OFFSET)

    def _write_to_nvm(self):
        return self.comm.write_data_with_response(bfuCommand.PROG_NVM)

    def display_metadata(self, meta):
        if meta is False:
            return False
        print("Display METADATA")
        print("****************")
        self.disable_telemetry()
        self.comm.write_data(bfuCommand.OUPUT_METADATA)
        if self.comm.wait_for_data() is False:
            return False
        result = self.comm.get_data_until(endMsg.END_NVM_LINE)
        print(result)
        self.comm.flush_all_input_data()
        self.enable_telemetry()
        print()  # Used for pretty message formatting only
        return True

    def display_nvm(self, show_nvm):
        if show_nvm is False:
            return False
        print("Display NVM")
        print("***********")
        self.disable_telemetry()
        self.comm.write_data(bfuCommand.OUPUT_NVM)
        if self.comm.wait_for_data() is False:
            return False
        for i in range(nvmInfo.NB_OF_NVM_PRINT_ROWS):
            result = self.comm.get_data_until(endMsg.END_NVM_LINE)
            print(hex(nvmInfo.NVM_START_ADDRS + i*16).upper(), " : ", result)
        self.comm.flush_all_input_data()
        self.enable_telemetry()
        print()  # Used for pretty message formatting only
        return True

    def _update_meta_string(self, nvm_data, meta_key):
        value_max_length_idx = list(nvm_data).index(meta_key)
        value_max_length = jsonInfo.NVM_STRINGS_SIZE[value_max_length_idx]
        value = nvm_data[meta_key]  # Value string to send
        value = value.ljust(value_max_length, " ")  # pad with spaces
        cmd = chr(bfuCommand.SN_NVM+list(nvm_data).index(meta_key))

        for iterator in range(value_max_length):
            cmd_msg = self._build_metadata_cmd(cmd, iterator, value[iterator])
            if self.comm.write_data_with_response(cmd_msg) is False:
                return False
        return True

    def _update_meta_int(self, nvm_data, int_key):
        cmd = 0
        if int_key == jsonInfo.AVAILABLE_NVM_INTEGERS[0]:
            cmd = bfuCommand.UPDATE_PAYLOAD_TIMER
        if int_key == jsonInfo.AVAILABLE_NVM_INTEGERS[1]:
            cmd = bfuCommand.UPDATE_ADC_AVERAGING
        if int_key == jsonInfo.AVAILABLE_NVM_INTEGERS[2]:
            cmd = bfuCommand.UPDATE_MUX_DELAY
        if int_key == jsonInfo.AVAILABLE_NVM_INTEGERS[3]:
            cmd = bfuCommand.UPDATE_FAN_PWM
        cmd = str(cmd) + str(nvm_data[int_key]).zfill(4)
        return self.comm.write_data_with_response(cmd)

    def update_calibration(self, calibrate):
        if calibrate is False:
            return False
        print("Starting BFU calibration")
        print("************************")
        self.disable_telemetry()
        if self.calibrate_chemresistor_offset() is True:
            ret = self._write_to_nvm()
        else:
            ret = False
        self.enable_telemetry()
        if ret is False:
            print("Error - Failure calibrating BFU\n")
        else:
            print("Successfully calibrated BFU\n")
        return ret

    def update_nvm(self, nvm_data):
        key = True
        ret = True
        for key in nvm_data.keys():
            if key in jsonInfo.AVAILABLE_NVM_META_STRINGS:
                ret = self._update_meta_string(nvm_data, key)
            if key in jsonInfo.AVAILABLE_NVM_INTEGERS:
                ret = self._update_meta_int(nvm_data, key)
            if ret is False:
                return False
        return self._write_to_nvm()

    def upload_new_cfig(self, cfig):
        if cfig is False:
            return
        print("Uploading configuration to NVM")
        print("*******************************")
        self.disable_telemetry()
        if self.update_nvm(cfig) is False:
            print("Error - Failure loading data to NVM\n")
        else:
            print("Successfully loaded data to NVM\n")
        self.enable_telemetry()

    def _print_telemetry_keys(self, data):
        tmp = []
        for x in range(len(data)):
            tmp.append(*data[x].keys())
        print(*tmp, sep='\t')

    def _print_telemetry_values(self, data):
        tmp = []
        for x in range(len(data)):
            tmp.append(*data[x].values())
        print(*tmp, sep='\t')

    def get_sensor_values(self, data):
        return data.values()

    def start_data_collection(self, ):
        #1 Create file
        #2 Update file with keys
        #3 start collecting data


    def display_telemetry(self, telemetry):
        if telemetry is False:
            return
        print("Starting telemetry collection")
        print("*****************************")
        sleep(bfuTiming.BFU_DELAY_BEFORE_CMD)
        self.comm.flush_all_input_data()
        first_iteration = True
        while 1:
            if self.comm.data_available():
                telem = str(self.comm.get_data_until(endMsg.END_NVM_LINE))
                telem = json.loads(telem)
                if first_iteration is True:
                    self._print_telemetry_keys(telem[jsonInfo.TELEMETRY_KEY])
                    first_iteration = False
                self._print_telemetry_values(telem[jsonInfo.TELEMETRY_KEY])
            sleep(1)
