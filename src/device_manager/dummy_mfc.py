import logging

logging.basicConfig(level=logging.DEBUG)


class MFC:
    def __init__(self, port, analyte):
        self.port = port
        self.analyte = analyte
        print(f"Dummy MFC on port {port}, with analyte: {analyte}")

        # self.value = value
        # print(f"Dummy MFC on port {port}, with analyte: {analyte}, value: {value}")

    def ensure_flow_rate(self, value):
        logging.debug(f"Ensuring Flow rate for MFC on {self.port} is value: {value}")
        print(f"MFC NAME: {self.port},VALUE: {value}")


if __name__ == "__main__":
    # A = MFC('COM3', 'potatoes', 'hello')
    A = MFC('COM3', 'potatoes')
