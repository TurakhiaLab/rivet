# Utility functions
#
#
import os.path
from termcolor import colored

def check_file_exists(file_path):
    """
    Check the given file_path exists, otherwise throw runtime error
    """
    if not os.path.isfile(file_path):
        print(colored("ERROR: {} file not found in current directory.".format(file_path), 'red', attrs=['reverse']))
        exit(1);
