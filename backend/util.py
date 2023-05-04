# Utility functions
#
#
import os.path
import secrets
from termcolor import colored

def check_file_exists(file_path):
    """
    Check the given file_path exists, otherwise throw runtime error
    """
    if not os.path.isfile(file_path):
        print(colored("ERROR: {} file not found in current directory.".format(file_path), 'red', attrs=['reverse']))
        exit(1);

def format_css(css):
    """
    Format a comma separated string
    If not present already:
        - Add a trailing space after comma
        - Remove trailing comma
    """
    css = css.replace(",",", ")
    # If trailing comma exists, remove it
    if (css[-1] == ","):
        css = css[:-1]
    return css

def css_to_list(css_string):
    """
    Convert a comma separated string to a list
    """
    lst = css_string.split(',')
    if (css_string[-1] == ","):
        del lst[-1]
    return lst

def generate_key():
    """
    """
    alphabet = string.ascii_letters.lower() + string.digits
    key = ''.join(secrets.choice(alphabet) for i in range(8))
    return key

def get_cache_config():
    """
    """
    config = {
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 300
    }
    return config
