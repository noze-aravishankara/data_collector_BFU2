import csv
import logging
import os
import sys
import threading
import time
from datetime import datetime as dt

import numpy as np

from CONFIG.config_parser import config_parser
from CONFIG.protocol_parser import protocol_parser
from device_manager.mfc_controller import MFC
from device_manager.BFU import BFU
from device_manager.PID import PID

logging.basicConfig(level=logging.INFO)

class data_collector:
    def __init__(self, config='CONFIG/config.json', protocol='CONFIG/test_protocol.json', log_level=logging.INFO):

        self._config = config_parser(config_file_path=config)
        self.config_dict = self._config.get_config_as_dict()
        self._protocol = protocol_parser(protocol_file_path=protocol)
        self.protocol_dict = self._protocol.get_protocol_as_dict()
        self.create_data_folder()
        self.device_setup(log_level)

        self.temp_thread_handler()

    def device_setup(self, log_level):
        self.devices = []
        for device in self._config.get_devices():
            x, y, z = self._config.get_device_info(device)
            fname = f'{self.directory}/{self.now_}_{self._config.get_output_file_prefix()}_{z}.csv'
            self.devices.append(BFU(port=x,
                                    baudrate=y,
                                    name=z,
                                    fname=fname,
                                    log_level=log_level))
        self.pid = PID(port=self.config_dict["PID"]["port"],
                       baudrate=self.config_dict["PID"]["baudrate"],
                       fname=f'{self.directory}/{self.now_}_{self._config.get_output_file_prefix()}_PID.csv')
        
        self.devices.append(self.pid)
        self.mfc_dict = {device: MFC(port=self.config_dict["MFC"][device]["port"], analyte=self.config_dict["MFC"][device]["analyte"]) for device in self.config_dict["MFC"]}
        


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

    def save_data_to_files(self, headers, data):
        for element in self.devices:
            f_name = f'{self.directory}/{self.now_}_{self._config.get_output_file_prefix()}_{element.name}.csv'
            with open(f_name, 'w', newline='') as g:
                logging.info(f"Saving data to: {f_name}")
                csv_writer = csv.writer(g, delimiter=',',)
                csv_writer.writerow(headers)
                csv_writer.writerows(data)
                g.close()

    def temp_thread_handler(self):
        self.threads = []
        for device in self.devices:
            device.data_collection_status = True
            _ = threading.Thread(target=device.continuous_collection)
            self.threads.append(_)
            _.start()
        self.temp_experiment_handler()

    def temp_experiment_handler(self):
        for step in self._protocol.get_step_names():
            _ = threading.Thread(target=self.step_timer2, args=(self._protocol.get_step_length(step),))
            for device in self.devices:
                device.trial_state = step
            for mfc in self.mfc_dict:
                value = self.protocol_dict[step]["MFC"][mfc]
                _2 = threading.Thread(target=self.mfc_dict[mfc].ensure_flow_rate, args=(value,), daemon=True)
                _2.start()
            logging.info(f'Setting {step} step for {self._protocol.get_step_length(step)} s')
            _.start()
            _.join()
        self.temp_end_thread_handler()

    def step_timer(self, sleep_time):
        time.sleep(sleep_time)
        logging.debug("Moving onto next step")

    def step_timer2(self, sleep_time):
        for i in range(sleep_time, 0, -1):
            time.sleep(1)
            if i < 4:
                logging.warning(f'Switching to next step in: {i}')

    def array_fixer(self, headers, array):
        _ = np.asarray(headers)
        _2 = np.asarray(array)
        print(_)

    def temp_end_thread_handler(self):
        for device in self.devices:
            device.data_collection_status = False
        logging.info('--------DONE DATA COLLECTION---------')


if __name__ == '__main__':
    level = logging.DEBUG
    DC = data_collector(config='CONFIG/config_with_mfc.json', protocol='CONFIG/test_protocol.json', log_level=level)