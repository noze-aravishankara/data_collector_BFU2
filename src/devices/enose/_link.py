"""

"""
import struct
import sys
import time
import threading


def synchronized(lock_name):
    """
    Synchronize a method for thread safety, using the specified lock.

    :param lock_name: the name of the lock object (instance variable)
    :return: the method synchronized using the lock object
    """

    def _wrap(method):
        def _synchronize_method(self, *args, **kwargs):
            lock = self.__getattribute__(lock_name)
            try:
                lock.acquire()
                # logger.debug("%s: ACQUIRED lock %s", method.__name__, lock)
                return method(self, *args, **kwargs)
            finally:
                lock.release()
                # logger.debug("%s: RELEASED lock %s", method.__name__, lock)

        return _synchronize_method

    return _wrap


def _crc8ccitt(crc=0x00, byte=None):
    """
    Calculate the CRC-8-CCITT checksum of the provided byte.

    :param crc: initial value
    :param byte: byte whose checksum is to be calculated
    :return: CRC-8-CCITT checksum
    """
    crc = crc ^ byte
    for i in range(8):
        crc = (crc << 1) ^ (0x07 if (crc & 0x80) else 0x00)
    crc &= 0xFF
    return crc


def _crc8ccitt_block(crc=0x00, block=None):
    """
    Calculate the CRC-8-CCITT checksum of the provided block.

    :param crc: initial value
    :param block: block whose checksum is to be calculated
    :return: CRC-8-CCITT checksum
    """
    crc = crc
    for i in range(len(block)):
        byte = ord(block[i])
        crc = _crc8ccitt(crc, byte)
    return crc


class DataLink(object):
    """
    Encapsulates a communications link at the frame level over a physical layer connection.

    """

    def __init__(self, connection=None, start=0x12, stop=0x13, escape=0x7d, checksum=_crc8ccitt_block, callback=None):
        """

        :param connection:
        :param start:
        :param stop:
        :param escape:
        :param checksum:
        :param callback:
        """
        self._connection = connection
        self._checksum = checksum
        self._stb = start
        self._etb = stop
        self._dle = escape
        self._callback = callback
        self._state = 0
        self._buffer = ''
        self.lock = threading.RLock()

    def _encode_byte(self, byte=None):
        """
        Encode a single byte for transmission.

        :param byte: (uint8)
        :return: (string) encoded byte
        """
        result = ''
        if byte in [self._stb, self._etb, self._dle]:
            result += chr(self._dle)
        result += chr(byte)
        return result

    def _encode_frame(self, opcode=None, payload=None):
        """
        Encode a frame for transmission.

        :param opcode: (uint8)
        :param payload: (string)
        :return: (string) encoded frame
        """
        frame = ''
        frame += self._encode_byte(byte=opcode)
        frame += self._encode_byte(byte=len(payload))
        for char in payload:
            byte = ord(char)
            frame += self._encode_byte(byte=byte)
        checksum = self._checksum(0x00, frame)
        frame += self._encode_byte(byte=checksum)
        return chr(self._stb) + frame + chr(self._etb)

    @synchronized('lock')
    def _read(self):
        """
        Decode a single byte from the input stream.

        If the end of a frame is detected, the frame is validated and a callback is triggered.

        :return: None
        """
        char = self._connection.read(1)
        if self._state == 0:
            if ord(char) == self._stb:
                self._state = 1
                return
            else:
                sys.stdout.write(char)
                return
        elif self._state == 1:
            if ord(char) == self._etb:
                checksum = self._checksum(0x00, self._buffer)
                if checksum != 0x00:
                    raise ValueError("Invalid checksum: {:02x} != 0x00".format(checksum))
                else:
                    opcode = ord(self._buffer[0])
                    self._callback(opcode, self._buffer[2:-1])
                self._state = 0
                self._buffer = ''
                return
            elif ord(char) == self._dle:
                self._state = 2
                return
            else:
                self._buffer += char
                return
        elif self._state == 2:
            self._buffer += char
            self._state = 1
            return

    @synchronized('lock')
    def read(self, size=1):
        """
        Decode the specified number of bytes from the input stream.

        If the end of a frame is detected, the frame is validated and a callback is triggered.

        :param size: number of bytes to decode
        :return: None
        """
        for i in range(size):
            self._read()

    @synchronized('lock')
    def read_all(self):
        """

        :return: None
        """
        count = self._connection.inWaiting()
        self.read(size=count)

    @synchronized('lock')
    def write(self, opcode=None, payload=None):
        """

        :param opcode:
        :param payload:
        :return: None
        """
        frame = self._encode_frame(opcode=opcode, payload=payload)
        self._connection.write(frame)
