import json


class protocol_parser:
    def __init__(self, protocol_file_path='test_protoco.json'):
        with open(protocol_file_path, 'r') as f:
            self.protocol = json.load(f)

    def get_protocol_as_dict(self):
        return self.protocol

    def get_baseline_length(self):
        return self.protocol['baseline']['length']

    def get_exposure_length(self):
        return self.protocol['exposure']['length']

    def get_recovery_length(self):
        return self.protocol['recovery']['length']


if __name__ == '__main__':
    A = protocol_parser('test_protocol.json')
    print(A.get_protocol_as_dict())
