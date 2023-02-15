import logging
import os
import datetime

class Singleton(object):
    def __new__(cls, *args, **kwds):
        it = cls.__dict__.get("__it__")
        if it is not None:
            return it
        cls.__it__ = it = object.__new__(cls)
        it.init(*args, **kwds)
        return it
    def init(self, *args, **kwds):
        pass


class Logger(Singleton):
    """

    """
    def init(self, name=None, handlers=None):
        out_dir = os.path.join(os.getcwd(), "log")
        if not os.path.isdir(out_dir):
            os.mkdir(out_dir)
        log_file_path = os.path.join(out_dir, datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")+".log")
        #formatter = logging.Formatter(
        #    fmt = '[%(asctime)s] [%(filename)s:%(lineno)d] [%(levelname)-8s] %(message)s',
        #    datefmt = '%F %H:%M:%S'
        #)
        self.name = name if name else "ROOT"
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        try:
            if handlers is None or handlers == []:
                handlers = [logging.FileHandler(log_file_path), logging.StreamHandler()]
                handlers[0].setLevel(logging.DEBUG)
                handlers[1].setLevel(logging.INFO)
        #        handlers[0].setFormatter(formatter)
        #        handlers[1].setFormatter(formatter)
                
        except:
            raise IOError("Could not create appropriate loggers")
        map(self.logger.addHandler, handlers)

    def info(self, msg):
        self.logger = logging.getLogger(self.name)
        self.logger.info(msg)

    def debug(self, msg):
        self.logger = logging.getLogger(self.name)
        self.logger.debug(msg)

    def warning(self, msg):
        self.logger = logging.getLogger(self.name)
        self.logger.warning(msg)

    def error(self, msg):
        self.logger = logging.getLogger(self.name)
        self.logger.error(msg)

    def critical(self, msg):
        self.logger = logging.getLogger(self.name)
        self.logger.error(msg)


def get_logger(name=None, handlers=None):
    return Logger(name, handlers)