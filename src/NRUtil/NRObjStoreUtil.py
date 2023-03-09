""" Utility module to make it easy to query and publish individual objects in
a bucket.

Works with constant file that makes the following env vars available:
OBJ_STORE_BUCKET    - Bucket name
OBJ_STORE_SECRET    - account secret access key (to access bucket)
OBJ_STORE_USER      - account name / access key id
OBJ_STORE_HOST      - object store host

"""

import logging
import os
from datetime import timedelta

import boto3
import minio

from . import constants

LOGGER = logging.getLogger(__name__)

name = __name__


class ObjectStoreUtil:
    def __init__(
        self,
        obj_store_host=None,
        obj_store_user=None,
        obj_store_secret=None,
        obj_store_bucket=None,
        tmpfolder=None,
    ):
        """[summary]

        :param obj_store_host: [if provided will use this as the object storage
                             host, if not will use the host described in the
                             environment variable: OBJ_STORE_HOST]
        :type obj_store_host: [type], optional
        :param obj_store_user: [description], defaults to None
        :type obj_store_user: [type], optional
        :param obj_store_secret: [description], defaults to None
        :type obj_store_secret: [type], optional
        """
        self.obj_store_host = obj_store_host
        self.obj_store_user = obj_store_user
        self.obj_store_secret = obj_store_secret
        self.obj_store_bucket = obj_store_bucket
        self.tmpfolder = tmpfolder

        if self.obj_store_host is None:
            self.obj_store_host = constants.OBJ_STORE_HOST
        if self.obj_store_user is None:
            self.obj_store_user = constants.OBJ_STORE_USER
        if self.obj_store_secret is None:
            self.obj_store_secret = constants.OBJ_STORE_SECRET
        if self.obj_store_bucket is None:
            self.obj_store_bucket = constants.OBJ_STORE_BUCKET
        # populate a temp folder variable.. if none is provided as an
        # arg or in a constants variable then just use the current
        # directory
        if self.tmpfolder is None:
            if hasattr(constants, "TMP_FOLDER"):
                self.tmpfolder = constants.TMP_FOLDER
            else:
                self.tmpfolder = os.path.dirname(__file__)

        LOGGER.debug(f"obj store host: {self.obj_store_host}")
        self.minio_client = minio.Minio(
            self.obj_store_host,
            self.obj_store_user,
            self.obj_store_secret,
        )
        # minio doesn't provide access to ACL's for buckets and objects
        # so using boto when that is required.  Methods that use the boto
        # client will create the object only when called
        self.boto_client = None
        self.boto_session = None

    def get_object(self, file_path, local_path, bucket_name=None):
        """extracts an object from object store to a location on the
        filesystem where code is being run.

        :param filePath: path to an object in objectstore
        :type filePath: str, path
        :param localPath: The path where the object should be copied to on
                          the local file system
        :type localPath: str, path
        :param bucketName: name of the bucket where the object is located, if
                           not provided uses the bucket that is identified in
                           the environment variable OBJ_STORE_BUCKET
        :type bucketName: str
        """
        if not bucket_name:
            bucket_name = self.obj_store_bucket
        retVal = self.minio_client.fget_object(
            bucket_name=bucket_name, object_name=file_path, file_path=local_path
        )
        LOGGER.debug(f"object get response: {self.get_obj_props_as_dict(retVal)}")

    def get_object_properties(self, object_name, bucket_name=None):
        return self.stat_object(object_name=object_name, bucket_name=bucket_name)

    def put_object(self, ostore_path, local_path, bucket_name=None):
        """just a wrapper method around the minio fput.  Makes it a
        little easier to call.

        :param localPath: the path to the file in the locally accessible file
                          system
        :type localPath: str
        :param destPath: the path in the object storage where the file should
                         be written.
        :type destPath:
        :param bucketName: [], defaults to None
        :type bucketName: [type], optional
        """
        if not bucket_name:
            bucket_name = self.obj_store_bucket

        ret_val = self.minio_client.fput_object(
            bucket_name=bucket_name, object_name=ostore_path, file_path=local_path
        )
        LOGGER.debug(f"object store returned: {self.get_obj_props_as_dict(ret_val)}")
        return ret_val

    def list_objects(
        self, objstore_dir=None, recursive=True, return_file_names_only=False
    ):
        """lists the objects in the object store.  Run's recursive, if
        inDir arg is provided only lists objects that fall under that
        directory

        :param inDir: The input directory who's objects are to be listed
                      if no value is provided will list all objects in the
                      bucket
        :type inDir: str
        :return: list of the object names in the bucket
        :rtype: list
        """
        objects = self.minio_client.list_objects(
            self.obj_store_bucket,
            recursive=recursive,
            prefix=objstore_dir,
            use_url_encoding_type=False,
        )
        retVal = objects
        if return_file_names_only:
            retVal = []
            for obj in objects:
                retVal.append(obj.object_name)

        return retVal

    def log_object_properties(self, in_object):
        """write to the log the properties / values of the specified
        object

        :param inObject: gets a python object and writes the property / values
                         to the debug log
        :type inObject: obj
        """
        for attr in dir(in_object):
            LOGGER.debug("obj.%s = %r" % (attr, getattr(in_object, attr)))

    def get_obj_props_as_dict(self, in_object):
        """Gets an object, iterates over the properties... any properties that
        do not start with a '_' are copied to a dict.  Not recursive, ie
        if properties are objects, then will just create an entry in the
        dictionary with value=object.

        :param inObject: The input object that is to be converted to a
                         dictionary
        :type inObject: obj
        :return: dictionary of the input object
        :rtype: dict
        """
        retDict = {}
        for attr in dir(in_object):
            if attr[0] != "_":
                retDict[attr] = getattr(in_object, attr)

        return retDict

    def stat_object(self, object_name, bucket_name=None):
        """runs stat on an object in the object store, returns the stat object

        :param objectName: name of the object to run stat on
        :type objectName: str
        """
        if bucket_name is None:
            bucket_name = self.obj_store_bucket
        stat = self.minio_client.stat_object(bucket_name, object_name)
        # self.__logObjectProperties(stat)
        return stat

    def createBotoClient(
        self, obj_store_user=None, obj_store_secret=None, obj_store_host=None
    ):
        """Checks to see if a boto connection has been made, if not then
        uses the following constants to build the connection:

        Treat this as a private method.  Any other methods that need a boto
        client will call this first.

        client id:      constants.OBJ_STORE_USER
        client secret:  constants.OBJ_STORE_SECRET
        s3 host:        constants.OBJ_STORE_HOST
        """
        self.obj_store_host
        if obj_store_user is None:
            obj_store_user = self.obj_store_user
        if obj_store_secret is None:
            obj_store_secret = self.obj_store_secret
        if obj_store_host is None:
            obj_store_host = self.obj_store_host

        if self.boto_session is None:
            self.boto_session = boto3.session.Session()

        # aws_access_key_id - A specific AWS access key ID.
        # aws_secret_access_key - A specific AWS secret access key.
        # region_name - The AWS Region where you want to create new
        #               connections.
        # profile_name - The profile to use when creating your session.

        if self.boto_client is None:
            self.boto_client = self.boto_session.client(
                service_name="s3",
                aws_access_key_id=obj_store_user,
                aws_secret_access_key=obj_store_secret,
                endpoint_url=f"https://{obj_store_host}",
            )

    def get_public_permission(self, object_name, bucket_name):
        """uses the boto3 module to communicate with the S3 service and retrieve
        the ACL's.  Parses the acl and return the permission that is associated
        with public access.

        :param objectName: name of the object who's permissions are to be
                           retrieved
        :type objectName: str
        :raises ValueError: error raise if more than one
        :return: the permission that is associated with public access to the
                 object if no public permission has been defined then returns
                 None.
        :rtype: str

        following is an example of the 'Grants' property of the object that is
        returned by the get_object_acl method

        Grants': [
            {
                'Grantee':
                    {'DisplayName': 'nr-wrf-prd',
                    'ID': 'nr-wrf-prd',
                    Type': 'CanonicalUser'},
                'Permission': 'FULL_CONTROL'
            },
           {
               'Grantee':
                    {'Type': 'Group',
                    'URI': 'http://acs.amazonaws.com/groups/global/AllUsers'},
                'Permission': 'READ'}]
            }

        ^^ where Grantee / Type is Group, URI is ALLUsers is what the method
        is looking for.  Also only expecting a single record that meets those
        criteria
        """
        if bucket_name is None:
            bucket_name = self.obj_store_bucket

        self.createBotoClient()
        permission = None
        results = self.boto_client.get_object_acl(Bucket=bucket_name, Key=object_name)
        LOGGER.debug(f"ACL permissions: {results}")
        for grants in results["Grants"]:
            if (
                "Grantee" in grants
                and "Type" in grants["Grantee"]
                and grants["Grantee"]["Type"] == "Group"
                and "URI" in grants["Grantee"]
                and "AllUsers".lower() in grants["Grantee"]["URI"].lower()
            ):
                if permission is not None:
                    msg = (
                        f"return object is: {results}, expecting it"
                        + "to only contain a single public permission but  "
                        + "have found >1. Public permissions are defined "
                        + 'under the property "Grants"-"Grantee"-"Type" = '
                        + "Group and allusers in the uri"
                    )
                    raise ValueError(msg)
                # print(f'grant:   {grants}')
                permission = grants["Permission"]
        return permission

    def set_public_permissions(self, object_name, bucket_name=None):
        """Sets the input object that exists in object store to be public
        Read.

        Using boto3 to accomplish this, but suspect that there is another way
        to do this, possibly interacting directly with the object store api.

        The following post: https://github.com/aws/aws-sdk-ruby/issues/2129
        suggests that you might be able to set the object as read when the
        data is uploaded by adding the parameter:

                x-amz-acl = public-read


        https://stackoverflow.com/questions/67315838/upload-images-as-image-jpeg-mime-type-from-flutter-to-s3-bucket/67848626#67848626

        :param objectName: [description]
        :type objectName: [type]
        """
        if bucket_name is None:
            bucket_name = self.obj_store_bucket
        self.createBotoClient()

        resp = self.boto_client.put_object_acl(
            ACL="public-read", Bucket=bucket_name, Key=object_name
        )
        LOGGER.debug(f"resp: {resp}")

    def get_force_download_headers(self, object_name):
        filename = os.path.basename(object_name)
        headers = {
            "content-type": "application/octet-stream",
            "Content-Disposition": f"attachment; filename={filename}",
            "response-content-type": "force-download",
            "response-content-disposition": f"attachment; filename={filename}",
        }
        return headers

    def get_presigned_url(
        self, object_name, object_bucket=None, expires=60 * 60, headers=None
    ):
        """
        Gets the name of an object and returns the presigned url

        :param objectName: object name / key that exists in the object store
        :type objectName: str
        """
        if object_bucket is None:
            object_bucket = self.obj_store_bucket

        if expires and isinstance(expires, int):
            expirestd = timedelta(seconds=expires)

        params = {"expires": expirestd}
        if headers is not None:
            params["response_headers"] = headers

        presignUrl = self.minio_client.get_presigned_url(
            "GET", object_bucket, object_name, **params
        )

        return presignUrl

    def delete_remote_file(self, dest_file, obj_store_bucket=None):
        """deletes a remote file

        :param dest_file: path to the remote file that is to be deleted
        """
        if not obj_store_bucket:
            obj_store_bucket = self.obj_store_bucket
        remove = self.minio_client.remove_object(obj_store_bucket, dest_file)
        LOGGER.debug(f"result of remove on {dest_file}: {remove}")
