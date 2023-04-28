import logging
import os.path
import shutil
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
def properties_advanced():
    """
    fixture that returns a dictionary with a bunch of values used for
    various tests, difference between this data and the normal property data is
    that this data recurses to a higher depth
    """
    # directory order is important.. make sure you list the root dir first
    # the sub dir, the sub/sub etc, as is show in data below.
    test_props = [
        {"test_file": "junk.txt", "test_dir": "junky"},
        {"test_file": "junk.txt", "test_dir": "junky/junky1"},
        {"test_file": "junk.txt", "test_dir": "junky/junky1/junk2"},
        {"test_file": "junk.txt", "test_dir": "junky/junky1/junk2/junk3"},
    ]
    finished_props = []
    for params in test_props:
        params["test_file_full_path"] = os.path.join(
            params["test_dir"], params["test_file"]
        )
        finished_props.append(params)

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

    ostore_object.put_object(ostore_path=dest_file, local_path=src_file)
    yield ostore_object
    if os.path.exists(src_file):
        os.remove(src_file)
    ostore_object.delete_remote_file(dest_file=dest_file)


@pytest.fixture(scope="module")
def ostore_w_more_data_local(ostore_object, properties_advanced):
    # make sure the directory doesn't exist in ostore
    root_dir = properties_advanced[0]["test_dir"]
    ostore_object.delete_directory(ostore_dir=root_dir)

    # setup creating local files to be synced
    for params in properties_advanced:
        if not os.path.exists(params["test_dir"]):
            os.makedirs(params["test_dir"])

        src_file = params["test_file_full_path"]
        LOGGER.debug(f"creating the file: {src_file}")
        with open(src_file, "w") as fh:
            fh.write("test 1 2 3\n")

    yield ostore_object

    # delete local files
    for params in properties_advanced:
        if os.path.exists(params["test_dir"]):
            shutil.rmtree(params["test_dir"])

        if os.path.exists(params["test_file_full_path"]):
            os.remove(params["test_file_full_path"])

    # delete ostore files if they exist
    ostore_object.delete_directory(ostore_dir=root_dir)
