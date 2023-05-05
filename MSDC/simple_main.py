import threading
import atexit
from datetime import datetime as dt
import os
import sys
import logging

logging.basicConfig(level=logging.DEBUG)

from CONFIG.config_parser import config_parser
from data_manager import data_manager
from device_manager import device_listener

class simple_dc:
    def __init__(self, config):
        self._config = config_parser(config_file_path=config).get_config_as_dict()    
        # CONNECT TO TEENSY
        #self.device = serial.Serial('/dev/ttyACM0', 115200)
        self.create_data_folder()
        fname = f'{self.directory}/{self.now_}_{self._config["output_file_prefix"]}_all.csv'
        self.device = device_listener('dev/ttyACM0', 115200, fname)
        atexit.register(self.exit_process)
        self.thread_handler()

    # CREATE DATA FILE
    def folder_info(self):
            self.now = dt.now()
            self.now_ = self.now.strftime("%y%m%d_%H%M")
            self.now_s = self.now.strftime("%y%m%d_%H%M%S")

    def create_data_folder(self):
        self.folder_info()
        self.directory = f'{self._config["output_directory"]}/' \
                        f'{self.now_}' \
                        f'_{self._config["output_file_prefix"]}'
        if not os.path.exists(self.directory):
            os.mkdir(self.directory)
        elif os.path.exists(self.directory):
            logging.warning('Folder Exists, adding seconds to folder name.')
            self.now_ = self.now_s
            self.directory = f'{self._config["output_directory"]}/' \
                        f'{self.now_}' \
                        f'_{self._config["output_file_prefix"]}'
            os.mkdir(self.directory)
        else:
            sys.exit()

    def thread_handler(self):
         self.device.run_status = True
         self.thread = threading.Thread(target=self.device.continuous_collection)
         self.thread.daemon = True
         self.thread.start()

    def exit_process(self):
         self.device.run_status = False
         logging.info('--------DONE DATA COLLECTION---------')