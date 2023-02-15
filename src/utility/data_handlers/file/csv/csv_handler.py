import os
import sys

from data_handlers.file.csv import writer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from data_handlers import base_handler

class CSVHandler(base_handler.ABCHandler):
    name = "csv_writer"
    def __init__(self, file_path, data_info, overwrite=True):
        self.file_path = file_path
        self.data_info = data_info
        self.initialize()

    @staticmethod
    def get_required_arguments_to_build():
        return {"file_path": None, "data_info": [], "overwrite": True}

    def initialize(self):
        writer.write(self.file_path, [self.data_info], True)

    def handle_new_data(self, data):
        writer.write(self.file_path, data, False)

    def terminate(self):
        pass
