import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.offline import init_notebook_mode, iplot
import re
from os import getcwd, listdir
from os.path import isdir
import logging

logging.basicConfig(level=logging.DEBUG)



class Plotter:
    def __init__(self, file_array, test_name='NO_NAME'):
        self.data = [pd.read_csv(f) for f in file_array]
        logging.info([f'Test shape: {df.shape}' for df in self.data])

    def baseline_data(self, arr):
        pass


if __name__ == '__main__':
    BFU1_test = ['humidity_data_BFU1/20230220_1544_PTFE-HUM-T002-V1-F10-R1/20230220_1544_PTFE-HUM-T002-V1-F10-R1_BFU0.csv',
                 'humidity_data_BFU1/20230220_1549_PTFE-HUM-T002-V1-F10-R2/20230220_1549_PTFE-HUM-T002-V1-F10-R2_BFU1.csv']

    BFU2_test = ['humidity_data_BFU2/230220_1544_PTFE-HUM-T002-V2-F10-R1/230220_1544_PTFE-HUM-T002-V2-F10-R1_BFU1.csv',
                 'humidity_data_BFU2/230220_1550_PTFE-HUM-T002-V2-F10-R2/230220_1550_PTFE-HUM-T002-V2-F10-R2_BFU2.csv']

    A = Plotter(BFU1_test)
    print(A.data[0].head())