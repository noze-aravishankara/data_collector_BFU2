import json


class protocol_parser:
    def __init__(self, protocol_file_path='test_protocol.json'):
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

    def get_num_steps(self):
        return len(self.protocol)

    def get_step_names(self):
        return [step for step in self.protocol.keys()]

    def get_step_length(self, step):
        return self.protocol[step]["length"]


if __name__ == '__main__':
    A = protocol_parser('test_protocol.json')
    print([A.get_step_length(elem) for elem in A.get_step_names()])
