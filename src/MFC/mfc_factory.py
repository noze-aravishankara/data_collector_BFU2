"""MFC factory module.

This module contains the MFCFactory class that implements the factory design pattern to create an ABCMFC type.

Example:
    >>> from mfc_factory import MFCFactory
    >>> MFCFactory.create_device("SensirionMFC", uniqueID="21450113")
"""

import logging

# from devices.enose._enose import ENose
from MFC.sensirion.sensirion_sfc500 import Sensirion_SFC500
from utility.logger import get_logger


class MFCFactory:
    """MFCFactory class that applies factory design pattern.

    Args:
        _MFCs (dict): Holds the available MFCs that can be created by this factory. If there is a new MFC
            implemented, this class variable must be updated.

    Todo:
        * Appropriate log messages must be added.
    """
    _MFCs = {Sensirion_SFC500.name: Sensirion_SFC500}

    @classmethod
    def get_mfc_lists(cls):
        """Returns list of all MFCs that can be created using this factory.

        Returns:
            ABCMFC: MFC that receives data.
        """
        return cls._MFCs.keys()

    @classmethod
    def get_mfc_required_arguments(cls, mfc_type):
        """Returns the required arguments to be passed to the specific mfc initializer.

        Args:
            mfc_type (string): Type of the device that must be created.

        Returns:
            dict: Dictionary containing parameters required for building a specific device.

        Todo:
            * The return value must be standardized.
        """
        return cls._MFCs[mfc_type].get_required_arguments_to_build()

    @classmethod
    def get_MFC_data_info(cls, mfc_type):
        """Returns the information related to each element in the data list that is received by the mfc.

        Args:
            mfc_type (string): Type of the device that must be created.

        Returns:
            list[string]: String values representing the elements in data list of the corresponding device.
        """
        return cls._MFCs[mfc_type].get_data_info()

    @classmethod
    def create_mfc(cls, mfc_type, **kwargs):
        """Creator method for the factory pattern.

        Args:
            mfc_type (string): Type of the device that must be created.
            **kwargs: Keyword Arguments that must be provided for the specific mfc.

        Returns:
            ABCMFC: A mfc object that inherits from the abstract base class ABCMFC.class

        Raises:
            Exception: If the device creation fails, an exception will be raised.
        """
        try:
            mfc = cls._MFCs[mfc_type.lower()]()
            initialized = mfc.initialize(**kwargs)
            if initialized:
                return mfc
            else:
                return None
        except Exception as e:
            get_logger().warning("Failed to create mfc due to :\n {}".format(e))
