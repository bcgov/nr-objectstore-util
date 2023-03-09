import logging
import os.path
import sys

import dotenv
import pytest

import NRUtil.constants
import NRUtil.NRObjStoreUtil

LOGGER = logging.getLogger(__name__)
LOGGER.debug(f"sys.path: {sys.path}")


@pytest.fixture(scope="module")
def properties():
    """
    fixture that returns a dictionary with a bunch of values used for
    various tests
    """
    test_props = {"test_file": "junk.txt", "test_dir": "junky"}
    test_props["test_file_full_path"] = os.path.join(
        test_props["test_dir"], test_props["test_file"]
    )
    yield test_props


@pytest.fixture(scope="module")
def ostore_object():
    LOGGER.debug(f"property is: {NRUtil.constants.module}")
    dotenv_file = os.path.join(os.path.dirname("__file__"), "..", "..", ".env")
    if os.path.exists(dotenv_file):
        dotenv.load_dotenv(dotenv_file)
        NRUtil.constants.set_properties(NRUtil.constants.ostore_env_vars_names)

    if not hasattr(NRUtil.constants, "OBJ_STORE_SECRET"):
        LOGGER.debug("the attribute doesn't exist")
    ostore = NRUtil.NRObjStoreUtil.ObjectStoreUtil()
    yield ostore


@pytest.fixture(scope="module")
def ostore_w_data(ostore_object, properties):
    test_file_full_path = properties["test_file_full_path"]
    src_file = properties["test_file"]
    dest_file = test_file_full_path
    with open(src_file, "w") as fh:
        fh.write("test 1 2 3\n")

    return_val = ostore_object.put_object(ostore_path=dest_file, local_path=src_file)
    yield ostore_object
    if os.path.exists(src_file):
        os.remove(src_file)
    ostore_object.delete_remote_file(dest_file=dest_file)
