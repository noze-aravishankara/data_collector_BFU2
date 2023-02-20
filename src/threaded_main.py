from CONFIG.config_parser import config_parser
from CONFIG.protocol_parser import protocol_parser
from device_manager.BFU import BFU
from datetime import datetime as dt
import numpy as np
import threading
import logging
import time
import csv
import sys
import os

logging.basicConfig(level=logging.INFO)


class data_collector:
    def __init__(self, config='CONFIG/config.json', protocol='CONFIG/test_protocol.json'):
        self._config = config_parser(config_file_path=config)
        self._protocol = protocol_parser(protocol_file_path=protocol)

        self.device_setup()
        self.create_data_folder()
        self.temp_thread_handler()

    def device_setup(self):
        self.devices = []
        for device in self._config.get_devices():
            x, y, z = self._config.get_device_info(device)
            self.devices.append(BFU(x, y, z))

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
            with open(f_name, 'w') as g:
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
            _ = threading.Thread(target=self.step_timer, args=(self._protocol.get_step_length(step),))
            for device in self.devices:
                device.trial_state = step
            logging.info(f'Setting {step} step for {self._protocol.get_step_length(step)} s')
            _.start()
            _.join()
        self.temp_end_thread_handler()

    def step_timer(self, sleep_time):
        time.sleep(sleep_time)
        logging.debug("Moving onto next step")

    def array_fixer(self, headers, array):
        _ = np.asarray(headers)
        _2 = np.asarray(array)
        print(_)

    def temp_end_thread_handler(self):
        for device in self.devices:
            device.data_collection_status = False
            headers = device.headers
            data = device.get_array()
            #self.array_fixer(headers, data)
            logging.debug(data)
            self.save_data_to_files(headers, data)


if __name__ == '__main__':
    DC = data_collector(config='CONFIG/config_single.json')