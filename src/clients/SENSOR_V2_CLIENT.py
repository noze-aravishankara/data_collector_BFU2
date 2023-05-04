import board
import busio

import atexit
import json
import adafruit_logging as logger

logging = logger.getLogger()
logging.setLevel(logger.DEBUG)

class NOZE_SENSOR_V2: 
    def __init__(self, tx, rx, name, baudrate=115200):
        self.sensor = busio.UART(tx, rx, baudrate=baudrate)
        self.name = name
        self.delimiter = bytes("\r\n\n", "ascii")
        logging.info(f"Creating sensor: {self.name}")
        
    def wait_for_data(self):
        if self.sensor.in_waiting > 0:
            return True
        else:
            return False
        
    def get_data(self):
        rx_data = self.sensor.readline().decode("utf-8")
        rx_data = str(self.sensor.readline().decode("utf-8"))
        rx_data = rx_data.replace("\n", "")
        rx_data = rx_data.replace("\r", "")
        rx_data = rx_data.replace("\x00", "")

        rx_data = json.loads(str(rx_data))
        
        return rx_data


    def get_new_data(self):
        while True:
            #logging.debug(f"{self.name} waiting for data")
            if self.sensor.in_waiting > 0:
                #logging.debug(f"{self.name} Got new data")
                rx_data = json.loads(self.sensor.readline().decode("utf-8"))
                # rx_data = rx_data.replace("\n", "")
                # rx_data = rx_data.replace("\r", "")
                # rx_data = rx_data.replace("\x00", "")
                # print(rx_data)
                return rx_data



if __name__ == "__main__":
    sensor = NOZE_SENSOR_V2(board.RX2, board.TX2)
    sensor.get_new_data()
            
    
