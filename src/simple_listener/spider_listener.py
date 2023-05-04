import logging
import os
import sys
import threading
import time
from datetime import datetime as dt
import numpy as np


class multi_data_collector:
    def __init__(self, config=None):
        self._config = config
        self.create_data_folder()

    def device_setup(self):
        
        
    
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

    def create_data_files(self):
        for element in self.devices:
            with open(f'{self.directory}/{self.now_}_{self._config.get_output_file_prefix()}'
                      f'_{element.name}.csv', 'w') as f:
                f.close()