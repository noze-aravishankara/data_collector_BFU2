import board
import busio
from SENSOR_V2_CLIENT import NOZE_SENSOR_V2 as NS2
import adafruit_logging as logger
import time

logging = logger.getLogger()
logging.setLevel(logger.DEBUG)


class INTERNAL_BOARD_SERVER:
    def __init__(self, sensors=None):
        self.load_sensors(sensors)
        self.run_status = False
        self.data = {}


    def load_sensors(self, sensors):
        if sensors == None:
            logging.info("No Sensors Connected!")
            self.exit_procedure()
        else:
            self.sensors = [NS2(sensors[sensor]["tx"], sensors[sensor]["rx"], sensors[sensor]["name"], sensors[sensor]["baudrate"]) for sensor in sensors]
            logging.info(f"There are {len(self.sensors)} sensors connected")

    def listener(self):
        while self.run_status:
            for sensor in self.sensors:
                if sensor.wait_for_data():
                    self.data[str(sensor.name)] = sensor.get_data()
                    logging.debug(f"I got data from sensor {sensor.name}")
                else:
                    pass

                if len(self.data) == len(self.sensors):
                    logging.debug("I have all the data")
                    print(self.data)
                    self.data = {}
                
                time.sleep(0.01)
    


    def exit_procedure(self):
        print("Exiting the system")


if __name__ =="__main__":
    sensors={
        "S1": {
            "tx": board.TX3,
            "rx":  board.RX3,
            "name": "dev1",
            "baudrate": 115200
        },
        "S2": {
            "tx": board.TX4,
            "rx":  board.RX4,
            "name": "dev2",
            "baudrate": 115200
        },
        "S3": {
            "tx": board.TX5,
            "rx":  board.RX5,
            "name": "dev3",
            "baudrate": 115200
        },
        "S4": {
            "tx": board.TX8,
            "rx":  board.RX8,
            "name": "dev4",
            "baudrate": 115200
        }
    }
    
    # WORKING CHANNELS ARE:
    # 3, 4, 5, 8
    
    sensors = {'S1': {
            'tx': board.TX8,
            'rx':  board.RX8,
            'name': "dev1",
            'baudrate': 115200
        }}

    server = INTERNAL_BOARD_SERVER(sensors=sensors)
    server.run_status = True
    server.listener()

    