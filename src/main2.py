import csv
import logging
import os
import sys
import threading
import time
from datetime import datetime as dt
import numpy as np
import serial
logging.basicConfig(level=logging.INFO)

from CONFIG.config_parser import config_parser
from CONFIG.protocol_parser import protocol_parser
from device_manager.BFU import BFU


class multi_data_collector:
    def __init__(self, config='CONFIG/config.json', protocol='CONFIG/test_protocol.json'):
        self._config = config_parser(config_file_path=config)
        
        self.create_data_folder()
        self.device_setup()

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
            logging.warning('Folder Exists, adding seconds to folder name.')
            self.now_ = self.now_s
            self.directory = f'{self._config.get_output_directory()}/' \
                         f'{self.now_}' \
                         f'_{self._config.get_output_file_prefix()}'
            os.mkdir(self.directory)
        else:
            sys.exit()

    def device_setup(self):
        self.device = serial.serial(self._config["devices"]["INTERNAL_SERVER"]["com_port"], self._config["devices"]["INTERNAL_SERVER"]["baud_rate"])
        for sensor in self._config["devices"]["SENSORS"]:
            fname = f'{self.directory}/{self.now_}_{self._config.get_output_file_prefix()}_{z}.csv'
                

    


