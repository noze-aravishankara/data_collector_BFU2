"""Device factory module.

This module contains the DeviceFactory class that implements the factory design pattern to create an ABCDevice type.

Example:
    >>> from device_factory import DeviceFactory
    >>> DeviceFactory.create_device("enose", connection="/dev/ttyUSB0") # for Linux
    >>> DeviceFactory.create_device("enose", connection="COM1") # for windows
"""

import logging

# from devices.enose._enose import ENose
from devices.enose.simple_enose import SimpleENose
from devices.enose.chamber_simple_enose import ChamberSimpleENose
from devices.additional.humidity import HumiditySensor
from devices.additional.arduino import Arduino
from devices.additional.ammonia import AmmoniaSensor
from devices.additional.co2 import CO2Sensor
from devices.additional.bme import BmeSensor
from devices.additional.autosampler import Autosampler
from utility.logger import get_logger





class DeviceFactory:
    """DeviceFactory class that applies factory design pattern.

    Args:
        _devices (dict): Holds the available devices that can be created by this factory. If there is a new device
            implemented, this class variable must be updated.

    Todo:
        * Appropriate log messages must be added.
    """
    _devices = {SimpleENose.name: SimpleENose,
                ChamberSimpleENose.name : ChamberSimpleENose,
                HumiditySensor.name: HumiditySensor,
                Arduino.name: Arduino,
                BmeSensor.name: BmeSensor,
                Autosampler.name: Autosampler,
                AmmoniaSensor.name: AmmoniaSensor,
                CO2Sensor.name: CO2Sensor}

    @classmethod
    def get_device_lists(cls):
        """Returns list of all devices that can be created using this factory.

        Returns:
            ABCDevice: Device that receives data.
        """
        return cls._devices.keys()

    @classmethod
    def get_device_required_arguments(cls, device_type):
        """Returns the required arguments to be passed to the specific device initializer.

        Args:
            device_type (string): Type of the device that must be created.

        Returns:
            dict: Dictionary containing parameters required for building a specific device.

        Todo:
            * The return value must be standardized.
        """
        return cls._devices[device_type].get_required_arguments_to_build()

    @classmethod
    def get_device_data_info(cls, device_type):
        """Returns the information related to each element in the data list that is received by the device.

        Args:
            device_type (string): Type of the device that must be created.

        Returns:
            list[string]: String values representing the elements in data list of the corresponding device.
        """
        return cls._devices[device_type].get_data_info()

    @classmethod
    def create_device(cls, device_type, **kwargs):
        """Creator method for the factory pattern.

        Args:
            device_type (string): Type of the device that must be created.
            **kwargs: Keyword Arguments that must be provided for the specific device.

        Returns:
            ABCDevice: A device object that inherits from the abstract base class ABCDevice.class

        Raises:
            Exception: If the device creation fails, an exception will be raised.
        """
        try:
            dev = cls._devices[device_type.lower()]()
            initialized = dev.initialize(**kwargs)
            if initialized:
                return dev
            else:
                return None
        except Exception as e:
            get_logger().warning("Failed to create device due to :\n {}".format(e))
