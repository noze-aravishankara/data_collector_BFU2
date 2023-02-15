"""

"""

import logging
import os
import sys
import yaml
#from .config_utils import _get_param_value
logging.basicConfig()
logger = logging.getLogger(__name__)


def _get_param_value(parsed_config, requested_key, mandatory=True):
    try:
        return parsed_config[requested_key]
    except KeyError:
        if mandatory:
            raise KeyError("{} is a mandatory configuration that is missing".format(requested_key))
        else:
            logging.warning("{} not found in configuration file. Default value will be used.".format(requested_key))
            return None


def read_yaml_file(path_to_file=None):
    """

    """
    try:
        with open(path_to_file, "r") as f:
            content = yaml.load(f)
            return content
    except Exception as e:
        logging.error("Could not read the file {} due to {}".format(path_to_file, e))
        raise

def prepare_output_directory(dir_path):
    out_dir = dir_path
    if not os.path.isdir(out_dir):
        out_dir = os.path.join(os.path.dirname(__file__), "..", "output")#_get_param_value(parsed_config, "output_directory"))
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)
    return out_dir



def manage_output(program_arguments, output_dir_name):
    """Creates the output directory and gets the name of the file through arguments or user input if not specified in the argument. Also prevents from overwriting.

    Args:
        program arguments (List[str]): Program's input arguments.
        output_dir_name (str): Name of the output directory. If not specified, the output directory will be named "outputs" at the same level as current file.

    Returns:
        str: String containing full path to the directory that should contain the output file and file's names' prefix.
    """
    if not output_dir_name:
        output_dir_name = "outputs"
        logging.info("Output directory name not specified. Using the default name: {}".format(output_dir_name))
    output_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", output_dir_name)
    valid_output_file = False
    if not os.path.isdir(output_directory):
        os.makedirs(output_directory)
    while not valid_output_file:
        if len(program_arguments) < 2:
            read_terminal_func = raw_input if sys.version_info[0] < 3 else input
            file_name_prefix = read_terminal_func("Please enter the output file name: \n")
        else:
            file_name_prefix = program_arguments[1]
        if not file_name_exists(output_directory, file_name_prefix, FILE_POSTFIX_SEPARATOR):
            valid_output_file = True
        else:
            logging.error("invalid output file name {}".format(file_name_prefix))
            program_arguments = program_arguments[:1]
    return os.path.join(output_directory, file_name_prefix)


def file_name_exists(directory, file_name_prefix, last_separator):
    """Checks if there is any file in the output directory with the given prefix.

    Args:
        directory (str): Intended directory.
        file_name_prefix (str): Prefix to be checked with the files' names in the directory.
        last_separator (char): Last character that specifies the prefix of the name. (exp. "abc_def_ghi.ext" the prefix will be abc_def for "_" as separator.)

    Returns:
        bool: True if there is a file with the given prefix and false if there is no file having the prefix.
    """
    files_names_in_directory = [os.path.splitext(f)[0]
                                for f in os.listdir(directory)
                                if os.path.isfile(os.path.join(directory, f))]
    return any([f[:f.rfind(last_separator)] == file_name_prefix for f in files_names_in_directory])    
