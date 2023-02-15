
import csv
import logging
from utility.logger import get_logger


logging.basicConfig(level=logging.DEBUG, format="[%(levelname)s] (%(threadName)-10s) %(message)s")


def write(file_path=None, data=None, overwrite=False):
    mode = "w+" if overwrite else "a+"
    if data is None or data == []:
        logging.debug("No data to write into the file {}".format(file_path))
        return
    with open(file_path, mode, newline='') as f:
        writer = csv.writer(f)
        for row in data:
            try:
                # get_logger().info("data: {}".format(data))
                # get_logger().info("row: {}".format(row))

                writer.writerow(row)
            except Exception as e:
                get_logger().info("Could not write line due to {}".format(e))
