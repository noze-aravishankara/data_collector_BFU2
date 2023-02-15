"""

"""
import logging
import os
import time

from utility.file_utils import read_yaml_file, prepare_output_directory

TYPE_READER = {"yaml": read_yaml_file}


class AppConfig:
    def __init__(self, path_to_file, file_type="yaml"):
        self._set_default_configuration()
        self._config = TYPE_READER[file_type](path_to_file)
        self._set_configuration(self._config)

        self._meta_data()


    def _set_default_configuration(self):
        self.cycle_period = 60
        self.master_temperature = 25
        self.output_file_prefix = str(int(time.time()))
        self.device_configs = []

    def _set_configuration(self, parsed_config):
        self.cycle_period = _get_param_value(parsed_config, "cycle_period", False)
        self.master_temperature = _get_param_value(parsed_config, "master_temperature", False)
        self.output_directory = prepare_output_directory(_get_param_value(parsed_config, "output_directory"))
        self.output_file_prefix = _get_param_value(parsed_config, "output_file_prefix", False)
        self.number_of_trials = _get_param_value(parsed_config, "number_of_trials", False)
        self.protocol = _get_param_value(parsed_config, "protocol", False)
        self.project = _get_param_value(parsed_config, "project", False)
        self.devices_configs = [DeviceConfig(device_name, device_params, self.master_temperature)
                                for device_name, device_params in parsed_config["devices"].items()]
        self.devices_list = [device_name for device_name in parsed_config["devices"].keys()]
        try:
            self.peripherals_configs = [PeripheralConfig(device_name, device_params, self.master_temperature)
                                        for device_name, device_params in parsed_config["peripherals"].items()]
            self.peripheral_list = [device_name for device_name in parsed_config["peripherals"].keys()]

        except:
            self.peripherals_configs = None
            self.peripheral_list = []

        try:
            self.MFC_configs = [MFCConfig(device_name, device_params, self.master_temperature)
                                for device_name, device_params in parsed_config["mfc"].items()]
            self.MFC_analyteList = [mfc_info['analyte'] for mfc_info in parsed_config['mfc'].values()]

        except:
            self.MFC_configs = None

    def _read_protocol(self,copy_path):
        import shutil
        cwd = os.getcwd()
        protocol_path = cwd + "\\" + str(self.protocol)
        copy_path = copy_path + "\\" + str(self.protocol)

        shutil.copy(protocol_path,copy_path)

        parsed_protocol = TYPE_READER["yaml"](protocol_path)
        self._trial_state = [state for state in parsed_protocol.keys()]
        self._trial_seconds = []
        total_cycle_seconds = 0
        params_seconds = [params for params in parsed_protocol.values()]
        for x in params_seconds:
            seconds = x['seconds']
            total_cycle_seconds += seconds
            self._trial_seconds.append(seconds)
        self.cycle_period = total_cycle_seconds if total_cycle_seconds > self.cycle_period else self.cycle_period

    def _meta_data(self):
        import csv

        try:
            path = os.path.join(self.output_directory + "\\" + self.output_file_prefix)
            os.mkdir(path)
        except Exception:
            pass

        self._read_protocol(path)



        prefix = self.output_file_prefix
        cycle_period = self.cycle_period
        device_list = self.devices_list
        protocol = self.protocol
        project = self.project
        perph = self.peripheral_list
        number_of_trial = self.number_of_trials
        mfc_analytelist = self.MFC_analyteList
        header = ["output_file_prefix", "cycle_period", "Devices id", "Protocol", "Number_of_trials", "project", "perpherial ",
                  "MFC_1", "MFC_2",
                  "MFC_3", "MFC_4", "MFC_5"]
        list = []
        list.extend((prefix,cycle_period, device_list, protocol, number_of_trial,project,perph))
        for mfc_name in mfc_analytelist:
            list.append(mfc_name)

        with open(path + '//' + 'metadata_{}.csv'.format(self.output_file_prefix), 'w', newline='') as f:
            writer = csv.writer(f)
            for w in range(len(list)):
                writer.writerow([header[w],list[w]])


            # writer.writerow(header)
            # writer.writerow(list)
        f.close()


class DeviceConfig:
    def __init__(self, name, device_params, master_temperature):
        self.name = name
        self.handlers = device_params["handlers"].copy()
        self.build_parameters = {k: device_params[k] for k in device_params if k != "handlers"}
        if "target_temperature" in self.build_parameters and master_temperature:
            self.build_parameters["target_temperature"] = master_temperature


class PeripheralConfig:
    def __init__(self, name, peripheral_params, master_temperature):
        self.name = name
        # self.handlers = device_params["handlers"].copy()
        self.build_parameters = {k: peripheral_params[k] for k in peripheral_params if k != "handlers"}
        if "target_temperature" in self.build_parameters and master_temperature:
            self.build_parameters["target_temperature"] = master_temperature


class MFCConfig:
    def __init__(self, name, MFC_params, master_temperature):
        self.name = name
        # self.handlers = device_params["handlers"].copy()
        self.build_parameters = {k: MFC_params[k] for k in MFC_params if k != "handlers"}
        if "target_temperature" in self.build_parameters and master_temperature:
            self.build_parameters["target_temperature"] = master_temperature


def _get_param_value(parsed_config, requested_key, mandatory=True):
    try:
        return parsed_config[requested_key]
    except KeyError:
        if mandatory:
            raise KeyError("{} is a mandatory configuration that is missing".format(requested_key))
        else:
            logging.warning("{} not found in configuration file. Default value will be used.".format(requested_key))
            return None
