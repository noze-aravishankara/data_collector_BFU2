import serial
from serialComm import SerialComm
import logging
import sys
import threading
from data_manager import data_manager as dm

logging.basicConfig(level=logging.DEBUG)

class device_listener:
    def __init__(self, port, baudrate, fname):
        #self.device = self.connect_to_device(port, baudrate)
        self.run_status = False
        self.name = 'TEENSY-INTERNAL'
        self.dm = dm(fname)

        try:
            self.device = self.connect_to_device()
            logging.info(f'Successfully connected to {self.name} on {self.port}')
        except:
            print(f'Could not connect. Port: {self.port} is not available.')
            sys.exit()

    def connect_to_device(self, port, baudrate):
        return SerialComm(port, baudrate)
    
    def get_new_data(self):
        while not self.device.data_available():
            pass
        else:
            _ = self.device.get_data()
            #logging.debug(_)
            self.update_file(_)
        return _

    def continuous_collection(self):
        while self.run_status:
            self.get_new_data()
        logging.info(f"Exititng Continuous Data collection loop")

    def update_file(self, data):
        _ = threading.Thread(target=self.dm.append_file, args=(data,))
        _.start()
        logging.debug('Updated CSV file')

        