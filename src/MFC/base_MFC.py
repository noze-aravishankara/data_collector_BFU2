"""Module containing abstract base class for any MFC device.

This module contains an IDevice abstract class that must be the parent class of every class that is responsible
for implementing the interface to a device/sensor/network that is sending data to the collection application.
"""

import abc


class ABCMFC:
    __metaclass__ = abc.ABCMeta
    protocol_execution = []
    name = None

    def __init__(self):
        self._initialized = False

    @abc.abstractmethod
    def initialize(self):
        """This method is responsible for initialization of the MFC.
        """
        raise NotImplementedError("Initialize method must be implemented.")

    @abc.abstractmethod
    def get_required_arguments_to_build(self):
        raise NotImplementedError("Method should be created to return the requirement arguments for object creation.")

    @abc.abstractmethod
    def get_header(self):
        """This method is responsible for returning the specifications of the device.
        """
        raise NotImplementedError("The method get_header must be implemented to return device information.")

    @abc.abstractmethod
    def get_data_info():
        """This method is responsible for returning the information regarding elements in data list received from the mfc.
            NOTE: Subclasses must implement this as a @staticmethod.
        """
        raise NotImplementedError("The method get_data_info must be implemented to return data elements information.")

    @abc.abstractmethod
    def get_data(self):
        """This method is responsible for fetching the data from the device and returning a list containing all the data received
            from the device and not been sent.
        """
        raise NotImplementedError("The method get_data must be implemented to return data from the device.")

    @abc.abstractmethod
    def terminate(self):
        """This method is responsible for termination of the connection and also taking required measurements to dispose the mfc object.
        """
        raise NotImplementedError(
            "The method terminate must be implemented to terminate the connection to device properly.")