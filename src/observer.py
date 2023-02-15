"""

"""
import copy
import os
import time

from data_handlers.handler_factory import HandlerFactory
from devices.device_factory import DeviceFactory
from MFC.mfc_factory import MFCFactory
from data_handlers.file.csv.csv_handler import CSVHandler
from utility.logger import get_logger


class Observer:
    DEVICE_LIST = ""
    CYCLE_TIME = int
    DEVICE_SIGNAL_STABILITY = []
    SYSTEM_STABLE = False
    NUMBER_OF_OBSERVERS = 0

    def __init__(self, device, handlers, monitors, additional_devices=[], mfc_devices=[]):

        self.status = None
        self.data = []
        self.device = device
        Observer.NUMBER_OF_OBSERVERS += 1
        self.signal_stable = False

        self.handlers = handlers
        self.monitors = monitors

        self.additional_devices = additional_devices
        self.mfc_devices = mfc_devices

        self.initalization()

    def initalization(self):
        cwd = os.path.dirname(os.path.realpath(__file__))
        get_logger().info("cwd_initalization:{}".format(cwd))
        data_headers = ["time_elapsed", "trial_state", "state_timeleft", "trial_id"]
        file_name = os.path.join(cwd, "monitor", "monitor.csv")

        for periph in self.additional_devices:
            if periph.name == "bme":
                data_headers.extend(periph.get_data_info())
        self.status = CSVHandler(file_name, data_headers)

    def update(self, time_elapsed, update_required, stability_check):

        def average_temperature(temperature_list):
            return sum(temperature_list) / len(temperature_list)

        self.data = self.device.get_data()
        # get_logger().info("# of devices list : {}".format(Observer.NUMBER_OF_OBSERVERS))
        # get_logger().info("signal_stability list before : {}".format(Observer.DEVICE_SIGNAL_STABILITY))
        # get_logger().info(" raw_data before : {}".format(self.data))

        if stability_check:
            self.signal_stable = self.device.get_stability(data=copy.deepcopy(self.data[0]))
            """
            THINGS TO DO:
            write method for get_stability() to evalulate the signal of each connected device
            and return a boolean that will tell us whether the signal is stable or not
            """

            # self.signal_stable = True

        else:
            Observer.DEVICE_SIGNAL_STABILITY = [False] * Observer.NUMBER_OF_OBSERVERS
            # get_logger('signal_stability list : {}'.format(Observer.DEVICE_SIGNAL_STABILITY))

        if self.signal_stable:
            """
            This "update' index finder wont work because its working on the assumption that other 
            devices will be and are stable. Might be fine if you absolutely need all TRUEs in list
            Actually.... it may work , revisit back to this later if actual index tracker is required.
            """
            update = Observer.DEVICE_SIGNAL_STABILITY.index(False)
            Observer.DEVICE_SIGNAL_STABILITY[update] = True
            # get_logger().info("signal_stability list after : {}".format(Observer.DEVICE_SIGNAL_STABILITY))
            self.signal_stable = False

        """
        THINGS TO DO :
        if all of the items in DEVICES_SIGNAL_STABILITY list are True then we will the signal to tell
        the MFC to change to the next state
        """
        if all(self.DEVICE_SIGNAL_STABILITY):
            get_logger().info("all devices are stable!!")

            if len(self.mfc_devices) > 0:
                activate_next_trial_state = self.mfc_devices[-1].get_trigger_required()
                # get_logger().info("activate next state : {}".format(activate_next_trial_state))
                if activate_next_trial_state:
                    for mfc in self.mfc_devices:
                        if mfc._groundtruth:
                            mfc._update_protocol()
                    for mfc in self.mfc_devices:
                        if mfc._enabled and not mfc._groundtruth:
                            mfc._update_protocol()

            Observer.DEVICE_SIGNAL_STABILITY = [False] * Observer.NUMBER_OF_OBSERVERS

        if len(self.mfc_devices) > 0:
            try:
                self.data = self.data[0]
                # get_logger().info("from MFC data : {}".format(self.data))

                if update_required:
                    mfc_info = self.mfc_devices[-1].get_status()
                    mfc_info = str(time_elapsed) + "," + mfc_info
                    mfc_info = mfc_info.split(",")
                    trial_elapsed, trial_state, exec_length, trial_id = mfc_info
                    self.status.handle_new_data([mfc_info])
                    get_logger().info(mfc_info)

                for mfc in self.mfc_devices:
                    try:
                        mfc_flowvalue = mfc.get_data()
                        if len(mfc_flowvalue.split(",")) > 1:
                            flow, state = mfc_flowvalue.split(",")
                            # get_logger().info("flow: {} w/ state: {}".format(flow, state))
                        else:
                            flow = mfc_flowvalue
                            # get_logger().info("flow: {} w no state".format(flow))
                        if flow == "None":
                            all_other_mfcs = self.mfc_devices[:]
                            all_other_mfcs.remove(mfc)
                            for error_mfc in all_other_mfcs:
                                error_mfc.reset_mfc()
                                time.sleep(1)
                            if len(mfc_flowvalue.split(",")) > 1:
                                flow, state = mfc_flowvalue.split(",")
                                mfc_flowvalue = str(-1) + "," + state
                            else:
                                mfc_flowvalue = str(-1)
                        try:
                            if len(mfc_flowvalue.split(",")) > 1:
                                for value in mfc_flowvalue.split(","):
                                    self.data.append(str(value))
                            else:
                                self.data.append(str(mfc_flowvalue))
                            # get_logger().info("appended {} to data: {}".format(mfc_flowvalue, self.data))
                        # try:
                        #     if :
                        #         mfc.update_protocol()

                        except Exception as e:
                            self.data = None
                            get_logger().warning("Dropping data  due to MFC failure to read flow value {}".format(e))
                    except Exception as e:
                        get_logger().warning("Unable to get_data from MFC {}".format(e))
            except Exception as e:
                self.data = None
                get_logger().warning("Dropping data due to BFU1/Kernel1 read error {}".format(e))


        else:
            try:
                self.data = self.data[0]
            except Exception as e:
                self.data = None
                self.data = None
                get_logger().warning("Dropping data due to {}".format(e))

        if len(self.additional_devices) > 0:
            try:
                current_temperature = []
                for periph in self.additional_devices:
                    extra_data = periph.get_data()
                    # get_logger().info("extra_data : {}".format(extra_data))
                    try:
                        # get_logger().info("my perph name is {}".format(periph.name))
                        if periph.name == "bme":
                            extra_data = extra_data.split("\r")[0].split(",")[0:2]
                            if update_required:
                                current_temperature.append(float(extra_data[0]))
                                mfc_info.extend(extra_data)
                            for value in extra_data:
                                self.data.append(float(value))
                                # self.data.append(float(extra_data[1]))
                        elif periph.name == "autosampler":
                            if len(extra_data.split(",")) > 1:
                                for new_value in extra_data.split("\r")[0].split(","):
                                    self.data.append(str(new_value))
                            else:
                                self.data.append(str(extra_data))
                            # get_logger().info(extra_data)
                        elif len(extra_data.split(",")) > 1:
                            for value in extra_data.split("\r")[0].split(","):
                                self.data.append(float(value))
                        else:
                            self.data.append(float(extra_data))
                    except Exception as e:
                        self.data = None
                        get_logger().warning("Dropping data dur to Peripheral device read error {}".format(e))
                # if update_required:
                #     self.status.handle_new_data([mfc_info])

                if len(current_temperature) > 0:
                    average_current_temperature = average_temperature(current_temperature)
                    # get_logger().info(
                    #     "current average temp: {} , trial_id: {}".format(average_current_temperature, trial_id))

                    for periph in self.additional_devices:
                        # get_logger().info(periph.name)
                        try:
                            if periph.name == "bme":
                                periph.shift_temperature(average_current_temperature, trial_id)
                                # get_logger().info(
                                #     "current average temp: {} , trial_id: {}".format(average_current_temperature,
                                #                                                      trial_id))
                                break
                        except Exception:
                            pass

            except Exception as e:
                self.data = None
                get_logger().warning("Dropping data drorue to BFU2  read er {}".format(e))

        if self.data is not None and self.data != []:
            for subs in self.handlers:
                subs.handle_new_data([self.data])
            for subs in self.monitors:
                subs.handle_new_data([self.data])

    def terminate(self):
        if len(self.additional_devices) > 0:
            for periph in self.additional_devices:
                periph.terminate()
                self.additional_devices.remove(periph)
        self.additional_devices = []
        if len(self.mfc_devices) > 0:
            for mfc in self.mfc_devices:
                mfc.terminate()
                # self.mfc_devices.remove(mfc)

                # time.sleep(1)
                # self.mfc_devices.remove(mfc)
        self.mfc_devices = []
        self.device.terminate()

        self.device = None


def create_observers(app_config):
    observers = []
    additional_devices = []
    mfc_devices = []

    devices = app_config.devices_list
    device_string = " ".join(devices).replace(" ", ",")

    total_cycle_time = app_config.cycle_period
    if app_config.peripherals_configs is not None:
        for pf in app_config.peripherals_configs:
            get_logger().info("Creating peripheral devices...")
            peripheral = DeviceFactory.create_device(**pf.build_parameters)
            if peripheral is not None:
                additional_devices.append(peripheral)
    for sfc in app_config.MFC_configs:
        get_logger().info("Creating MFC devices...")
        sfc_device = MFCFactory.create_mfc(**sfc.build_parameters)
        if sfc_device is not None:
            mfc_devices.append(sfc_device)
    for dc in app_config.devices_configs:
        device = DeviceFactory.create_device(**dc.build_parameters)
        if device:
            device_data_info = device.get_data_info()
            if len(mfc_devices) > 0:
                for mfc in mfc_devices:
                    device_data_info.extend(mfc.get_data_info())
            if len(additional_devices) > 0:
                for periph in additional_devices:
                    device_data_info.extend(periph.get_data_info())

            monitor_handlers = dc.handlers.copy()
            handlers = create_handlers(device, dc.handlers, app_config, dc.name, device_data_info)
            monitors = create_monitor(device, monitor_handlers, app_config, dc.name, device_data_info)
            observers.append(Observer(device, handlers, monitors, additional_devices, mfc_devices))

    # Observer.DEVICE_LIST = device_string
    Observer.CYCLE_TIME = total_cycle_time
    return observers


def create_handlers(device, handlers_dict, app_config, device_name, handler_data_info_param):
    for h_type in handlers_dict:
        build_args = HandlerFactory.get_handlers_required_arguments(h_type)
        build_args["data_info"] = device.get_data_info()
        build_args.update(handlers_dict[h_type])
        if "csv_writer" in handlers_dict:
            # try:
            #     path = os.path.join(app_config.output_directory + "\\" + app_config.output_file_prefix)
            #     os.mkdir(path)
            # except OSError:
            #     pass
            config_path = str(handlers_dict["csv_writer"]["file_path"]).encode()
            handlers_dict["csv_writer"]["file_path"] = config_path if config_path else \
                os.path.join(app_config.output_directory, app_config.output_file_prefix,
                             app_config.output_file_prefix + "_" + str(device_name) + ".csv")
            # get_logger().info("output_dir: {}".format(app_config.output_directory))
            # get_logger().info("handlers_dict: {}".format(handlers_dict))
    handlers = [
        HandlerFactory.create_handler(k, **merge_dictionaries(handlers_dict[k], {"data_info": handler_data_info_param}))
        for k in handlers_dict]
    # get_logger().info("handlers_list: {}".format(handlers))

    return handlers


def create_monitor(device, monitor_dict, app_config, device_name, handler_data_info_param):
    for h_type in monitor_dict:
        build_args = HandlerFactory.get_handlers_required_arguments(h_type)
        build_args["data_info"] = device.get_data_info()
        build_args.update(monitor_dict[h_type])
        if "csv_writer" in monitor_dict:
            # config_path = str(monitor_dict["csv_writer"]["file_path"]).encode()
            monitor_dict["csv_writer"]["file_path"] = os.path.join(
                app_config.monitor_directory,
                app_config.output_file_prefix + "_" + str(device_name) + ".csv")
            # get_logger().info("monitor_dir: {}".format(app_config.monitor_directory))
            # get_logger().info("monitor_dict : {}".format(monitor_dict))

    monitors = [
        HandlerFactory.create_handler(k, **merge_dictionaries(monitor_dict[k], {"data_info": handler_data_info_param}))
        for k in monitor_dict]
    return monitors


def create_update(device, monitor_dict, app_config, device_name, handler_data_info_param):
    for h_type in monitor_dict:
        build_args = HandlerFactory.get_handlers_required_arguments(h_type)
        build_args["data_info"] = device.get_data_info()
        build_args.update(monitor_dict[h_type])
        if "csv_writer" in monitor_dict:
            # config_path = str(monitor_dict["csv_writer"]["file_path"]).encode()
            monitor_dict["csv_writer"]["file_path"] = os.path.join(
                app_config.monitor_directory,
                app_config.output_file_prefix + "_" + str(device_name) + ".csv")
            # get_logger().info("monitor_dir: {}".format(app_config.monitor_directory))
            # get_logger().info("monitor_dict : {}".format(monitor_dict))

    monitors = [
        HandlerFactory.create_handler(k, **merge_dictionaries(monitor_dict[k], {"data_info": handler_data_info_param}))
        for k in monitor_dict]
    return monitors


def merge_dictionaries(d1, d2):
    d3 = d1.copy()
    d3.update(d2)
    return d3
