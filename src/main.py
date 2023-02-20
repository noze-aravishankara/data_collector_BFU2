from CONFIG.config_parser import config_parser
from CONFIG.protocol_parser import protocol_parser
from device_handler.BFU_RUNNER2 import *
import sys
import os
from datetime import datetime as dt
import time
from csv import writer
import threading
import logging
import numpy as np
logging.basicConfig(level=logging.INFO)


class BFU2:
    """
    ----------------PROPERTY OF NOZE----------------

    TITLE: BFU 2 - Data Collector

    Description:
        This class connects to any number of BFUs and collects data based
        on a protocol file and config file (located in CONFIG/). The data will
        be output to a folder in output. The default version of this app
        works with BFU 2. With some modifications, it can work with BFU 1.

        Notable issues:
        1. If the serial number of the BFU 2 is changed, then the
        sensor will output data at approximately 2Hz. To fix this we have to
        re-flash the sensor. This is an issue that needs to addressed.


    Attributes:
        Config File: Can be found in CONFIG/config.json. Follow the defined in the file.

        Timeout Rate: The time at which to timeout from the connection (optional)
    Outputs:
        Connection Status: If the connection succeeded or not
        The current data output

    =====================================
    Current Version: 1.0 - February 16, 2023
    =====================================
    Revisions: [NONE]


    TO-DOs:
        1. Add concurrency
        2. Respond to protocol file


    Authors(s):
    Adi Ravishankara (aravishankara@noze.ca)

    ------------------------------------------------
    """
    def __init__(self, config='CONFIG/config.json', protocol='CONFIG/test_protocol.json'):
        # Obtaining test settings from config and protocol file
        self._config = config_parser(config_file_path=config)
        self.config = self._config.get_config_as_dict()
        self._protocol = protocol_parser(protocol)
        self.protocol = self._protocol.get_protocol_as_dict()

        # Initializing the system
        self.device_setup()
        #self.create_data_folder()
        #self.create_data_files()

        # Running the test
        self.threaded_temp_run_test()
        # self.temp_run_test()

    def device_setup(self):
        self.devices = [BFU_RUNNER(self._config.get_device_com_port(device), self._config.get_device_name(device))
                        for device in self._config.get_devices()]
        print(f'Number of BFUs Connected: {len(self.devices)}')

    def folder_info(self):
        self.now = dt.now()
        self.now_ = self.now.strftime("%y%m%d_%H%M")
        self.now_s = self.now.strftime("%y%m%d_%H%M%S")

    def create_data_folder(self):
        self.folder_info()
        self.directory = f'{self._config.get_output_directory()}/' \
                         f'{self.now_}' \
                         f'_{self._config.get_output_file_prefix()}'
        if not os.path.exists(self.directory):
            os.mkdir(self.directory)
        elif os.path.exists(self.directory):
            print('Folder Exists, adding seconds to folder name.')
            self.now_ = self.now_s
            self.directory = f'{self._config.get_output_directory()}/' \
                         f'{self.now_}' \
                         f'_{self._config.get_output_file_prefix()}'
            os.mkdir(self.directory)
        else:
            sys.exit()

    def create_data_files(self):
        for element in self.devices:
            with open(f'{self.directory}/{self.now_}_{self._config.get_output_file_prefix()}'
                      f'_{element.name}.csv', 'w') as f:
                f.close()

    def temp_run_test(self):
        for i in range(10):
            for j in self.devices:
                j.get_new_data()
        for j in self.devices:
            M = j.get_complete_array()
            print(M)
            #M = np.array(M)
            #print(M.shape)

    def threaded_temp_run_test(self):
        self.threads = []
        for j in self.devices:
            _ = threading.Thread(target=j.temporary_data_collector(10))
            logging.info(f"Inside the thread of: {j.name} ")
            self.threads.append(_)
            _.start()

        for j in self.threads:
            j.join()

        for j in self.devices:
            print(j.get_complete_array())


if __name__ == '__main__':
    BFU2 = BFU2()

