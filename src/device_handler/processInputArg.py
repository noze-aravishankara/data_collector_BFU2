#!/usr/bin/env python3

"""
Company     : NOZE
Author      : Eddy Fraga
Created on  : January 20, 2023
File type   : python
File name   : BFU_RUNNER.py
Description : Python interface class to process the main script input parameters.
Reference   : N/A
"""

import json
import platform
import sys

from serial.tools.list_ports import comports

from constants import options, compatibleOS, portInfo, jsonInfo


class ProcessInputArg:
    def args_received(self, input_arguments):
        if len(input_arguments) == 1:
            print("Error - No input arguments detected.")
            return False
        return True

    # NOT NEEDED
    def cfig_file_in_arg(self, arg):
        cfig = [s for s in arg if s.endswith(options.CFIG_FILE_EXT)]
        if len(cfig) == 0:
            return False
        if len(cfig) > 1:
            print("Error - Too many configuration files passed as input arguments")
            return False
        return list(arg).index(cfig[0])

    # NOT NEEDED
    def open_cfig_file(self, file):
        try:
            with open(file, 'r', encoding="utf8") as cfig_file:
                cfig = json.load(cfig_file)  # Convert json cfig file to dict.
                return cfig
        except:
            print("Error - Can't open configuration file: ", file)
            return None

    # NOT NEEDED
    def validate_cfig(self, cfig):
        for key in cfig.keys():
            if key in jsonInfo.AVAILABLE_NVM_META_STRINGS:
                expect_len = jsonInfo.NVM_STRINGS_SIZE[list(cfig).index(key)]
                length = len(cfig[key])
                if length > expect_len:
                    print("Error - Configuration file", key, "=", cfig[key])
                    print(length, "characters detected, but expecting ", expect_len)
                    return False
            if key in jsonInfo.AVAILABLE_NVM_INTEGERS:
                if cfig[key].isdigit() is False:
                    print("Error - Configuration file", key, "=", cfig[key])
                    print("Value must be an integer.")
                    return False
        return cfig

    # NOT NEEDED
    def process_cfig_arg(self, arg):
        cfig_arg_index = self.cfig_file_in_arg(arg)
        if cfig_arg_index is False:
            return False
        cfig = self.open_cfig_file(sys.argv[cfig_arg_index])
        if cfig is None:
            return False
        return self.validate_cfig(cfig)

    def process_arg_options(self, arg):
        opts = [s for s in arg if s.startswith(options.ARG)]
        if len(opts) == 0:
            return False
        return opts

    def process_comm_arg(self, arg):
        comm = []
        if platform.system() == compatibleOS.LINUX:
            comm = [s for s in arg if s.startswith(portInfo.COMM_LINUX)]
        if platform.system() == compatibleOS.WINDOWS:
            comm = [s for s in arg if s.startswith(portInfo.COMM_WIN)]
        if len(comm) != 1:
            return False
        return comm[0]

    def validate_comm_arg(self, comm):
        if comm is False:
            print("Error - Missing or incorrect comm. port argument")
            return False
        return True
    # NOT NEEDED
    def validate_cfig_arg(self, cfig, opt):
        # logic = Err. with config file but option is OK
        logic1 = (cfig is False) and (self.process_opt_update_nvm(opt))

        # logic = Config file OK but option is incorrect
        logic2 = (cfig is not False) and (not self.process_opt_update_nvm(opt))

        if (logic1 or logic2):
            print("Error - Configuration file incorrect or missing '-u' option")
            return False
        return True

    def process_args(self, input_arguments):
        if self.args_received(input_arguments) is False:
            return False, False, False
        opt = self.process_arg_options(input_arguments)
        cfig = self.process_cfig_arg(input_arguments)
        com = self.process_comm_arg(input_arguments)
        return com, cfig, opt

    def display_available_port(self):
        for port in comports():
            print(port)

    def process_help_opt(self, opt):
        if (opt is False) or (options.HELP not in opt):
            return False
        print("\nAPPLICATION HELP INFO:")
        print("**********************")
        print("Usage\t\t: python bfuTool.py [port] [option] [NVM config file]")
        print("Example\t\t: python bfuTool.py COM1 -u -n -t bfuConfigTemplate.json\n")
        print("Available system serial ports:")
        self.display_available_port()
        print("\nAvailable options:")
        print(options.HELP,
              "\t\t: show this help message and exit (Won't run other options)")
        print(options.METADATA, "\t\t: print metadata")
        print(options.UPDATE_NVM,
              "\t\t: Update NVM (valid configuration. file argument required)")
        print(options.SHOW_NVM, "\t\t: print NVM")
        print(options.TELEMETRY, "\t\t: print telemetry data (continuous)")
        print(options.CALIB, "\t\t: ADC offset calibration\n")
        print("NVM cfig file\t: BFU NVM JSON configuration file (e.g.: bfuConfigTemplate.json)\n")
        return True

    def process_opt_update_nvm(self, opt):
        if (opt is False) or (options.UPDATE_NVM not in opt):
            return False
        return True

    def process_opt_calib(self, opt):
        if (opt is False) or (options.CALIB not in opt):
            return False
        return True

    def process_opt_metadata(self, opt):
        if (opt is False) or (options.METADATA not in opt):
            return False
        return True

    def process_opt_telemetry(self, opt):
        if (opt is False) or (options.TELEMETRY not in opt):
            return False
        return True

    def process_opt_show_nvm(self, opt):
        if (opt is False) or (options.SHOW_NVM not in opt):
            return False
        return True
