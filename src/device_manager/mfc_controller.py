from sensirion_shdlc_driver.errors import ShdlcDeviceError
from sensirion_shdlc_driver import ShdlcSerialPort, ShdlcConnection
from sensirion_shdlc_sfc5xxx import Sfc5xxxShdlcDevice, Sfc5xxxScaling, \
    Sfc5xxxValveInputSource, Sfc5xxxUnitPrefix, Sfc5xxxUnit, \
    Sfc5xxxUnitTimeBase, Sfc5xxxMediumUnit
import logging
from time import sleep

logging.basicConfig(level=logging.INFO)

# POTATO
class MFC:
    def __init__(self, port, analyte=None):
        _ = ShdlcSerialPort(port=port, baudrate=115200)
        self.device = Sfc5xxxShdlcDevice(ShdlcConnection(_), slave_address=0)
        self.unit = Sfc5xxxMediumUnit(
        Sfc5xxxUnitPrefix.MILLI,
        Sfc5xxxUnit.STANDARD_LITER,
        Sfc5xxxUnitTimeBase.MINUTE)
        
        self.port = port
        self.analyte = analyte
        self.scaling = Sfc5xxxScaling.USER_DEFINED
        self.sn = self.get_serial_number()
        self.device.set_user_defined_medium_unit(self.unit)
        self.threshold = 10 # in sccm
        self.current_setpoint = 0

        if analyte is not None:
            logging.info(f"MFC on port {self.port} with SN: {self.sn} is {analyte}")
        else:
            logging.info(f'MFC on port {self.port} has SN: {self.sn}')

    def get_serial_number(self):
        _ = self.device.get_serial_number()
        logging.debug(f'Device connected on port {self.port} has serial number: {_}')
        return _
    
    def get_current_flow_value(self):
        _ = self.device.read_measured_value(scaling=self.scaling)
        logging.debug(f'Current Flow value for MFC on port {self.port} is {_}')
        return _
    
    def set_flow_rate(self, value):
        self.current_setpoint = value
        logging.debug(f'Setting the flow value to {value} sccm')
        try:
            self.device.set_setpoint(self.current_setpoint, scaling=self.scaling)
        except Exception as e:
            logging.warn(f"MFC on port {self.port} with analyte {self.analyte} raised the following issue: {e}. Device status is {self.device.read_device_status()}")


    def ensure_flow_rate(self, value):
        logging.debug(f"Ensuring Flow rate for MFC on {self.port} is value: {value}")
        self.set_flow_rate(value=value)
        while abs(self.get_current_flow_value()-self.current_setpoint) > self.threshold:
            logging.warning(f'MFC on port {self.port} with analyte {self.analyte} flow rate is {self.get_current_flow_value()}. Set point is {self.current_setpoint}')
            # self.set_flow_rate(value)
            sleep(0.1)

    def test_run(self):
        val = 0
        while val != 999:
            val = int(input('Type in 0 to turn off, 1 to turn on, 999 to exit the system: '))
            if val == 999:
                break
            else:
                self.ensure_flow_rate(val)
        self.exit_procedure()

    def exit_procedure(self):
        self.set_flow_rate(0)
        logging.info("Exiting the system")

        


if __name__ == "__main__":
    A = MFC("COM8", "acetone")
    A.test_run()
