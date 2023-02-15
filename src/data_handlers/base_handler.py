
"""Module containing abstract base class for any data handler such as file writer, plotter, ...

This module contains an ABCHandler abstract class that must be the parent class of every class that is responsible
for handling the data that is received from any device type object.
"""

import abc

class ABCHandler:
    name = None
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self._initialized = False

    @abc.abstractmethod
    def initialize(self):
        """This method is responsible for initialization of the handler.
        """
        raise NotImplementedError("Initialize method must be implemented.")

    @abc.abstractmethod     
    def handle_new_data(self):
        """This method is responsible for handling new data received from any device.
        """
        raise NotImplementedError("The method get_header must be implemented to handle the new received data.")

    @abc.abstractmethod
    def get_required_arguments_to_build(self):
        """
        """
        raise NotImplementedError("Method should be created to return the requirement arguments for handler object creation.")

    @abc.abstractmethod
    def terminate(self):
        """This method is responsible for termination process of the handler.
        """
        raise NotImplementedError("The method terminate must be implemented to terminate the handler.")