import json


class config_parser:
    def __init__(self, config_file_path='CONFIG/config.json'):
        with open(config_file_path, 'r') as f:
            self.config = json.load(f)

    def get_config_as_dict(self):
        return self.config

    def get_output_directory(self):
        return self.config['output_directory']

    def get_protocol_file_path(self):
        return self.config['protocol_file']

    def get_output_file_prefix(self):
        return self.config['output_file_prefix']

    def get_num_devices(self):
        return len(self.config['devices'])

    def get_devices(self):
        return self.config['devices'].keys()

    def get_device_com_port(self, device='device0'):
        return self.config['devices'][device]['com_port']

    def get_device_baudrate(self, device='device0'):
        return self.config['devices'][device]['baud_rate']

    def get_device_name(self, device='device0'):
        return self.config['devices'][device]['device_name']

    def get_device_info(self, device='device0'):
        return self.get_device_com_port(device), self.get_device_baudrate(device), self.get_device_name(device)

    def get_project_name(self):
        return self.config['project_name']


if __name__ == '__main__':
    A = config_parser('config.json')
    print(A.get_devices())