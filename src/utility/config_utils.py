"""

"""
import sys
from datetime import datetime
import logging
from utility import config_utils, file_utils, logger
import os
import time

from utility.file_utils import read_yaml_file, prepare_output_directory, prepare_monitor_directory, read_json_file, \
    logger
from utility.logger import get_logger

TYPE_READER = {"yaml": read_yaml_file,
               "json": read_json_file}


class AppConfig:
    number_of_trials = 0
    mfc_protocol = {}

    def __init__(self, path_to_file, file_type="yaml"):
        cwd = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        logging.info("cwd from app: {}".format(cwd))
        path_to_file = os.path.join(cwd, path_to_file)
        self._set_default_configuration()
        self._config = TYPE_READER[file_type](path_to_file)
        self._set_configuration(self._config)

    def _set_default_configuration(self):
        self.cycle_period = 60
        self.master_temperature = 25
        self.output_file_prefix = str(int(time.time()))
        self.device_configs = []

    def _set_configuration(self, parsed_config):
        self.cycle_period = _get_param_value(parsed_config, "cycle_period", False)
        self.stability_window = _get_param_value(parsed_config, "stability_window", False)
        self.master_temperature = _get_param_value(parsed_config, "master_temperature", False)
        self.temperature_control = _get_param_value(parsed_config, "temperature_control", False)
        self.demo_mode = _get_param_value(parsed_config, "demo_mode", False)
        self.monitor_directory = prepare_monitor_directory(_get_param_value(parsed_config, "monitor_directory"))
        self.output_directory = prepare_output_directory(_get_param_value(parsed_config, "output_directory"))

        self.output_file_prefix = str(datetime.today().strftime('%Y%m%d_%H%M_')) + _get_param_value(parsed_config,
                                                                                                    "output_file_prefix",
                                                                                                    False)
        AppConfig.number_of_trials = _get_param_value(parsed_config, "number_of_trials", False)
        self.protocol_name = _get_param_value(parsed_config, "protocol", False)
        self.project = _get_param_value(parsed_config, "project", False)
        self.devices_configs = [DeviceConfig(device_name, device_params, self.master_temperature)
                                for device_name, device_params in parsed_config["devices"].items()]
        self.devices_list = [device_name for device_name in parsed_config["devices"].keys()]

        self._chamberID_1 = []
        self._chamberID_2 = []
        self._chamberID_3 = []
        self._chamberID_4 = []
        for device_name, device_params in parsed_config["devices"].items():
            if device_params["chamber_id"] == "1":
                self._chamberID_1.append(device_name)
            if device_params["chamber_id"] == "2":
                self._chamberID_2.append(device_name)
            if device_params["chamber_id"] == "3":
                self._chamberID_3.append(device_name)
            if device_params["chamber_id"] == "4":
                self._chamberID_4.append(device_name)

        try:
            self.MFC_analyteList = [mfc_info['analyte'] for mfc_info in parsed_config['mfc'].values()]
        except:
            self.MFC_analyteList = []

        try:
            self.peripheral_list = [device_name for device_name in parsed_config["peripherals"].keys()]
        except:
            self.peripheral_list = []

        self._meta_data()
        try:
            self.peripherals_configs = [
                PeripheralConfig(device_name, device_params, self.master_temperature, self.temperature_control,
                                 self.demo_mode)
                for device_name, device_params in parsed_config["peripherals"].items()]

        except:
            self.peripherals_configs = None
            self.peripheral_list = []


        try:
            self.MFC_configs = [MFCConfig(device_name, device_params, self.master_temperature)
                                for device_name, device_params in parsed_config["mfc"].items()]
        except:
            self.MFC_configs = None

    def _read_protocol(self, output_path):
        import shutil
        cwd = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

        protocol_path = os.path.join(cwd, 'CONFIG', str(self.protocol_name))
        output_path = os.path.join(output_path, str(self.protocol_name))

        shutil.copy(protocol_path, output_path)

        parsed_protocol = TYPE_READER["yaml"](protocol_path)
        AppConfig.mfc_protocol = parsed_protocol
        self._trial_state = [state for state in parsed_protocol.keys()]
        self._trial_seconds = []
        total_cycle_seconds = 0
        params_seconds = [params for params in parsed_protocol.values()]
        for x in params_seconds:
            seconds = x['seconds']
            total_cycle_seconds += seconds
            self._trial_seconds.append(seconds)
        total_cycle_seconds = total_cycle_seconds * self.number_of_trials
        self.cycle_period = total_cycle_seconds if total_cycle_seconds > self.cycle_period else self.cycle_period

    def _meta_data(self):
        import csv
        device_string = ''
        periph_string = ''
        try:
            ROOT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
            get_logger().info("ROOT_DIR {}".format(ROOT_DIR))
            path = os.path.join(ROOT_DIR, self.output_directory, self.output_file_prefix)

            os.mkdir(path)
        except Exception:
            pass

        self._read_protocol(path)

        prefix = self.output_file_prefix
        cycle_period = self.cycle_period
        device_string = " ".join(self.devices_list).replace(" ", ",")
        periph_string = " ".join(self.peripheral_list).replace(" ", ",")
        chamberID1_string = " ".join(self._chamberID_1).replace(" ", ",")
        chamberID2_string = " ".join(self._chamberID_2).replace(" ", ",")
        chamberID3_string = " ".join(self._chamberID_3).replace(" ", ",")
        chamberID4_string = " ".join(self._chamberID_4).replace(" ", ",")

        protocol_name = self.protocol_name
        project = self.project
        perph = self.peripheral_list
        number_of_trials = AppConfig.number_of_trials
        mfc_analytelist = self.MFC_analyteList
        header = ["output_file_prefix", "cycle_period", "device_id", "protocol", "number_of_trials", "project",
                  "perpherial ", "mfc_1", "mfc_2", "mfc_3", "mfc_4", "mfc_5",
                  "chamber_1", "chamber_2", "chamber_3", "chamber_4"]

        list = []
        list.extend((prefix, cycle_period, device_string, protocol_name, number_of_trials, project, periph_string))
        for mfc_name in mfc_analytelist:
            list.append(mfc_name)
        list.extend((chamberID1_string, chamberID2_string, chamberID3_string, chamberID4_string))

        meta_data_file = path + '//' + '{}.csv'.format(self.output_file_prefix)
        with open(meta_data_file, 'w', newline='') as f:
            writer = csv.writer(f)
            for w in range(len(list)):
                writer.writerow([header[w], list[w]])

            # writer.writerow(header)
            # writer.writerow(list)
        f.close()

        try:
            import shutil
            shutil.copy(meta_data_file, self.monitor_directory)
        except:
            pass


class DeviceConfig:
    def __init__(self, name, device_params, master_temperature):
        self.name = name
        self.handlers = device_params["handlers"].copy()
        self.build_parameters = {k: device_params[k] for k in device_params if k != "handlers"}
        if "target_temperature" in self.build_parameters and master_temperature:
            self.build_parameters["target_temperature"] = master_temperature


class PeripheralConfig:
    def __init__(self, name, peripheral_params, master_temperature, temperature_control, demo_mode):
        self.name = name
        # self.handlers = device_params["handlers"].copy()
        self.build_parameters = {k: peripheral_params[k] for k in peripheral_params if k != "handlers"}
        if "target_temperature" in self.build_parameters and master_temperature:
            self.build_parameters["target_temperature"] = master_temperature
        if temperature_control and name == "bme":
            self.build_parameters["temperature_control"] = temperature_control
        if demo_mode:
            get_logger().info("were here")
            self.build_parameters["demo_mode"] = demo_mode
            self.build_parameters["number_of_trials"] = AppConfig.number_of_trials
            self.build_parameters["protocol"] = AppConfig.mfc_protocol


class MFCConfig:
    def __init__(self, name, MFC_params, master_temperature):
        self.name = name
        # self.handlers = device_params["handlers"].copy()
        self.build_parameters = {k: MFC_params[k] for k in MFC_params if k != "handlers"}
        if "target_temperature" in self.build_parameters and master_temperature:
            self.build_parameters["target_temperature"] = master_temperature
        self.build_parameters["number_of_trials"] = AppConfig.number_of_trials
        self.build_parameters["protocol"] = AppConfig.mfc_protocol


def _get_param_value(parsed_config, requested_key, mandatory=True):
    try:
        return parsed_config[requested_key]
    except KeyError:
        if mandatory:
            raise KeyError("{} is a mandatory configuration that is missing".format(requested_key))
        else:
            logging.warning("{} not found in configuration file. Default value will be used.".format(requested_key))
            return None
