import logging
import os.path

import minio
import pytest
import requests

import NRUtil.NRObjStoreUtil

LOGGER = logging.getLogger(__name__)


def test_get_fam_application_nodata(ostore_object):
    LOGGER.debug("got here")
    # make sure the ostore_object works
    assert ostore_object is not None
    buckets = ostore_object.minio_client.list_buckets()
    bucket_names = [bucket.name for bucket in buckets]
    LOGGER.debug(f"bucket names: {bucket_names}")
    assert ostore_object.obj_store_bucket in bucket_names


def test_put_object(ostore_object):
    src_file = "junk.txt"
    dest_file = "junky/junk.txt"
    with open(src_file, "w") as fh:
        fh.write("test 1 2 3\n")

    return_val = ostore_object.put_object(ostore_path=dest_file, local_path=src_file)
    assert return_val.object_name == dest_file

    if os.path.exists(src_file):
        os.remove(src_file)


def test_list_objects(ostore_w_data, properties):
    obj_list = ostore_w_data.list_objects(
        objstore_dir="junky", return_file_names_only=True
    )

    assert properties["test_file_full_path"] in obj_list


def test_make_public(ostore_w_data, properties):
    ostore = ostore_w_data

    obj_props = ostore.get_object_properties(
        object_name=properties["test_file_full_path"]
    )

    obj_props_dict = ostore.get_obj_props_as_dict(obj_props)
    LOGGER.debug(f"obj_props_dict: {obj_props_dict}")
    obj_url = (
        f'https://{ostore.obj_store_host}/{ostore.obj_store_bucket}' +
        f'/{obj_props_dict["object_name"]}'
    )
    LOGGER.debug(f"url: {obj_url}")
    resp = requests.get(obj_url)
    LOGGER.debug(f"resp.status_code: {resp.status_code}")
    assert resp.status_code == 403
    ostore.set_public_permissions(object_name=properties["test_file_full_path"])
    resp = requests.get(obj_url)
    LOGGER.debug(f"resp.status_code: {resp.status_code}")
    assert resp.status_code == 200


def test_presign(ostore_w_data, properties):
    ostore = ostore_w_data

    url = ostore.get_presigned_url(
        object_name=properties["test_file_full_path"], expires=60
    )
    r = requests.get(url)
    LOGGER.debug(f"status_code: {r.status_code}")
    assert r.status_code == 200
    LOGGER.debug(f"presigned url: {url}")


def test_update_ostore(ostore_w_more_data_local, properties_advanced):
    """tests the function that updates a directory.  It should only upload
    files if they do not already exist in the object store.

    :param ostore_w_data: _description_
    """
    ostore = ostore_w_more_data_local

    # sanity testing, making sure the fixture did what we expected.
    for param in properties_advanced:
        LOGGER.debug(f'fullpath: {param["test_file_full_path"]}')
        assert os.path.exists(param["test_file_full_path"])
        # assert doesn't exist in ostore
        with pytest.raises(minio.error.S3Error):
            ostore.get_object_properties(
                object_name=param["test_file_full_path"]
            )

    # now run sync
    dest_dir = properties_advanced[0]["test_dir"]
    src_dir = os.path.realpath(dest_dir)

    ostore = NRUtil.NRObjStoreUtil.ObjectStoreDirectorySync(
        src_dir=src_dir, dest_dir=dest_dir
    )
    ostore.update_ostore_dir()

    # make sure the files exist in ostore
    ostore_file_list = ostore.list_objects(
        objstore_dir=dest_dir, return_file_names_only=True
    )
    for param in properties_advanced:
        assert param["test_file_full_path"] in ostore_file_list
