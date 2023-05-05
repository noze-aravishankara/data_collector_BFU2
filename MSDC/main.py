import csv
import logging
import os
import sys
import threading
import time
from datetime import datetime as dt
import numpy as np
import serial
import json
import atexit

logging.basicConfig(level=logging.DEBUG)

from CONFIG.config_parser import config_parser
from data_manager import data_manager


class multi_data_collector:
    def __init__(self, config='CONFIG/config.json'):
        self._config = config_parser(config_file_path=config).get_config_as_dict()
        self.run_status = False
        atexit.register(self.exit_process())
        self.create_data_folder()
        self.device_setup()
        #self.single_time_listener()
        self.thread_handler()

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

    def device_setup(self):
        self.device = serial.Serial(self._config["devices"]["INTERNAL_SERVER"]["com_port"], self._config["devices"]["INTERNAL_SERVER"]["baud_rate"])
        self.dms = {}
        for sensor in self._config["devices"]["SENSORS"]:
            self.dms[sensor] = data_manager(f'{self.directory}/{self.now_}_{self._config["output_file_prefix"]}_{sensor}.csv')

    def thread_handler(self):
        self.run_status = True
        self.thread = threading.Thread(target=self.continuous_multi_listener)
        self.thread.daemon = True
        self.thread.start()

    def continuous_multi_listener(self):
        while self.run_status:
            if self.device.in_waiting > 0:
                _ = json.loads(str(self.device.readline().decode("utf-8")))
                logging.debug('Got New Data')
                # for sensor in _:
                #     _2 = threading.Thread(target=self.dms[sensor].append_file, args=(_['t'],))
                #     _2.start()
            
            
    def exit_process(self):
        logging.info("--- ENDING DATA COLLECTION ---")
        #self.thread.join()
        self.run_status = False
        sys.exit()

    def single_time_listener(self):
        headers = False
        self.device.flush()
        logging.debug('Initializing the headers, and flush')
        while self.wait_for_data() == False:
            logging.info('Waiting for data')
            time.sleep(0.01)
        logging.info('Exiting loop')
        _ = str(self.device.readline().decode("utf-8"))
        logging.debug('Got the data')

        # while not headers:
        #     logging.debug('inside while loop 1')
        #     if self.device.in_waiting > 0:
        #         _data = json.loads(str(self.device.readline().decode("utf-8")))
        #         keys = self.update_file_with_headers(_data["dev1"])
        #         for sensor in self.dms:
        #             self.dms[sensor].append_file(keys)
        #         logging.info('Done Updating Headers')
        #         headers = True
        #     else:
        #         logging.debug('Waiting for headers')

    def wait_for_data(self):
        if self.device.in_waiting > 0:
            return True
        else:
            return False


    def update_file_with_headers(self, data):
        _ = self.get_new_data()
        _ = [list(d.keys())[0] for d in _['t']]
        return _
    
    

        


                

    

if __name__ == "__main__":
    A = multi_data_collector()
