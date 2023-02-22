import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.offline import init_notebook_mode, iplot
import re
from os import getcwd, listdir
from os.path import isdir
import logging

logging.basicConfig(level=logging.INFO)



class Plotter:
    def __init__(self, file_array, test_name='NO_NAME'):
        self.data = [pd.read_csv(f) for f in file_array]
        logging.info([f'Test shape: {df.shape}' for df in self.data])

        self.fig = go.Figure()

    def baseline_data(self, arr):
        pass

    def gen_figure(self, data):
        for element in data:
            logging.info(element)
            self.fig.add_trace(
                go.Scatter(
                    visible=False,
                    line=dict(color="#00CED1", width=3),
                    name=element,
                    y=A[element],
                ),
            )

    def show_figure(self):
        self.fig.show()


if __name__ == '__main__':
    BFU1_test = ['humidity_data_BFU1/20230220_1544_PTFE-HUM-T002-V1-F10-R1/20230220_1544_PTFE-HUM-T002-V1-F10-R1_BFU0.csv',
                 'humidity_data_BFU1/20230220_1549_PTFE-HUM-T002-V1-F10-R2/20230220_1549_PTFE-HUM-T002-V1-F10-R2_BFU1.csv']

    BFU2_test = ['humidity_data_BFU2/230220_1544_PTFE-HUM-T002-V2-F10-R1/230220_1544_PTFE-HUM-T002-V2-F10-R1_BFU1.csv',
                 'humidity_data_BFU2/230220_1550_PTFE-HUM-T002-V2-F10-R2/230220_1550_PTFE-HUM-T002-V2-F10-R2_BFU2.csv']

    A = Plotter(BFU2_test)
    A.gen_figure(A.data)
    A.show_figure()
