""" Declaring constants used by the archive script. """

import logging
import os
import sys

import dotenv

LOGGER = logging.getLogger(__name__)

envPath = os.path.join(os.path.dirname(__file__), '.env')

module = sys.modules[__name__]

if os.path.exists(envPath):
    print("loading dot env...")
    dotenv.load_dotenv()


def set_properties(env_var_names: list):
    """gets a list of possible env variables.  Searches for them and populates
    constant variables with the same name if they exist.

    :param env_var_names: a list of env var names that the script will copy
        into properties with the same name
    """
    for env_var_name in env_var_names:
        if env_var_name in os.environ:
            setattr(module, env_var_name, os.environ[env_var_name])

# searching for default object store env variables and populate into constants
# if they exist
ostore_env_vars_names = ['OBJ_STORE_BUCKET', 'OBJ_STORE_SECRET',
                         'OBJ_STORE_USER', 'OBJ_STORE_HOST']
set_properties(ostore_env_vars_names)

# other optional params
optionals = ['TEST_OBJ_NAME']
set_properties(optionals)
