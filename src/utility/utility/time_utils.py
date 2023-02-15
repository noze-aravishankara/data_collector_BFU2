"""Time utility module.

This module contains utilities related to time.

Example:
    To use functions in this module import the module or just the function.:
    >>> from time_utils import get_unix_timestamp
    >>> get_unix_timestamp()
    1524752702594

"""

import time

def get_unix_timestamp():
    """Returns the Unix time of the system in milliseconds.

    Returns:
        float: Number representing the Unix time in milliseconds.
    """
    return int(time.time()*1000)