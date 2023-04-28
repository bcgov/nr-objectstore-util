""" Utility module to make it easy to query and publish individual objects in
a bucket.

Works with constant file that makes the following env vars available:
OBJ_STORE_BUCKET    - Bucket name
OBJ_STORE_SECRET    - account secret access key (to access bucket)
OBJ_STORE_USER      - account name / access key id
OBJ_STORE_HOST      - object store host

"""

import glob
import hashlib
import logging
import os
import pathlib
import posixpath
import sys
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
        self.part_size = 15728640

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
        LOGGER.debug("object get response:" + f"{self.get_obj_props_as_dict(retVal)}")

    def get_object_properties(self, object_name, bucket_name=None):
        return self.stat_object(object_name=object_name, bucket_name=bucket_name)

    def put_object(self, ostore_path, local_path, bucket_name=None, public=False):
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
        metadata = {}
        if public:
            metadata = {"x-amz-acl": "public-read"}

        ret_val = self.minio_client.fput_object(
            bucket_name=bucket_name,
            object_name=ostore_path,
            file_path=local_path,
            part_size=self.part_size,
            metadata=metadata,
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

    def delete_directory(self, ostore_dir, obj_store_bucket=None):
        """deletes all the objects inside the directory"""
        obj_list = self.list_objects(
            objstore_dir=ostore_dir, return_file_names_only=True
        )
        for obj_name in obj_list:
            self.delete_remote_file(dest_file=obj_name)


class ObjectStoreDirectorySync(ObjectStoreUtil):
    def __init__(
        self,
        src_dir,
        dest_dir,
        obj_store_host=None,
        obj_store_user=None,
        obj_store_secret=None,
        obj_store_bucket=None,
    ):
        ObjectStoreUtil.__init__(
            self,
            obj_store_host=obj_store_host,
            obj_store_user=obj_store_user,
            obj_store_secret=obj_store_secret,
            obj_store_bucket=obj_store_bucket,
        )

        self.src_dir = src_dir
        self.dest_dir = dest_dir
        self.obj_store_host = obj_store_host
        self.obj_store_user = obj_store_user
        self.obj_store_secret = obj_store_secret
        self.obj_store_bucket = obj_store_bucket

        if self.obj_store_host is None:
            self.obj_store_host = constants.OBJ_STORE_HOST
        if self.obj_store_user is None:
            self.obj_store_user = constants.OBJ_STORE_USER
        if self.obj_store_secret is None:
            self.obj_store_secret = constants.OBJ_STORE_SECRET
        if self.obj_store_bucket is None:
            self.obj_store_bucket = constants.OBJ_STORE_BUCKET

        # figure out what has already been copied
        self.ostore_cache = None
        self._calc_cache()
        self.ostore_paths = ObjectStoragePathLib(
            obj_store_host=obj_store_host,
            obj_store_user=obj_store_user,
            obj_store_secret=obj_store_secret,
            obj_store_bucket=obj_store_bucket,
        )

    def _calc_cache(self):
        """creates an in memory data struct that makes it easy to determine
        if a destination file already exists or not
        """
        LOGGER.info("retrieving a list of objects in object storage...")
        remote_dir_file_list = self.list_objects(
            objstore_dir=self.dest_dir, recursive=True, return_file_names_only=False
        )

        # creating in memory lookup struct that will be used to determine what
        # objects exist in ostore and which ones do not.
        ostore_objs_struct = []
        LOGGER.info("indexing the list of objects for faster lookup...")
        for ostore_obj in remote_dir_file_list:
            # file_path, file_name = os.path.split(ostore_obj.object_name)
            # if file_path not in ostore_objs_struct:
            # ostore_objs_struct[file_path] = []
            # ostore_objs_struct[file_path].append(file_name)
            ostore_objs_struct.append(ostore_obj.object_name)
        self.ostore_cache = tuple(ostore_objs_struct)

    def _exists(self, dest_file):
        objDoesExist = False
        if dest_file in self.ostore_cache:
            objDoesExist = True
        return objDoesExist

    # def update_ostore_dir(
    #     self, src_dir: str, dest_dir: str, obj_store_bucket: str = None
    # ):
    #     """updates a remote directory with files that exist locally but do not
    #     exist in object storage.  If a file exists remotely its assumed that
    #     the local version is the same.  Currently no checking takes place to
    #     see if an existing file has been updated.  Only updates for missing
    #     files.

    #     :param src_dir: The path to the local directory that needs to by
    #         copied and / or updated with the directory that is remote
    #     :param dest_dir: The path in object storage that the `src_dir` should
    #         be copied to
    #     :param obj_store_bucket: (optional) The name of the destination bucket.
    #         defaults to the bucket that gets defined in the environment
    #         variable OBJ_STORE_BUCKET
    #     """

    def update_ostore_dir(
        self,
        src_dir=None,
        dest_dir=None,
        delete=False,
        public=False,
        obj_store_bucket: str = None,
    ):
        """Recursive copy of directory contents to object store.

        Iterates over all the files and directoris in the 'src_dir' parameter,
        when the iteration finds a directory it calls itself with that
        directory

        does a file list of the dest_dir in object store... only copies files
        if the equivalent destination file does not already exist in object
        storage.

        :param src_dir: input directory that is to be copied
        :type src_dir: str
        :param dest_dir: destination directory that is to be copied
        :type dest_dir: str
        :param delete: after file has been copied whether to delete the local
            version or not
        :type delete: bool
        :param public: whether to make the destination file a public object or
           not.  If set to true the url path to the object will be public/read
           permissions.  If false will require the secrets to be able to view
           the file.
        :type public: bool
        :param obj_store_bucket: override the bucket destination.  If use this
            parameter the bucket needs to accessible by the same credentials
            used to setup the minio/boto3 client
        :param obj_store_bucket: str
        """
        if src_dir is None:
            src_dir = self.src_dir
        if dest_dir is None:
            dest_dir = self.dest_dir
        for local_file in glob.glob(src_dir + "/**"):
            LOGGER.debug(f"local_file: {local_file}")
            obj_store_path = self.ostore_paths.get_obj_store_path(
                src_path=local_file,
                ostore_path=self.dest_dir,
                src_root_dir=self.src_dir,
                prepend_bucket=False,
            )
            LOGGER.debug(f"objStorePath: {obj_store_path}")
            if not os.path.isfile(local_file):
                self.update_ostore_dir(
                    src_dir=local_file,
                    dest_dir=obj_store_path,
                    delete=delete,
                    public=public,
                    obj_store_bucket=obj_store_bucket,
                )
            else:
                # if the path is a file path check if it already exists in
                # ostore and then copy
                if not self._exists(obj_store_path):
                    # TODO: call the inheriting class to do the copy
                    LOGGER.debug(f"uploading: {local_file} to {obj_store_path}")
                    self.put_object(
                        ostore_path=obj_store_path, local_path=local_file, public=public
                    )
                if delete:
                    LOGGER.debug(f"removing the local file: {local_file}")
                    os.remove(local_file)

    def _verify(self, local_file, dest_file):
        """identifis if the local file and the dest file are the same file by
        checking the md5 hash cached in object storage and the version that
        has been stored locally.

        :param local_file: file path to the local version of the file
        :param dest_file: file path to the equivalent file in object storage
        """
        dest_obj_info = self.minio_client.get_object(self.obj_store_bucket, dest_file)
        etagDest = dest_obj_info.etag

        is_same = False

        md5Src = hashlib.md5(open(local_file, "rb").read()).hexdigest()
        LOGGER.debug(f"etagDest: {etagDest}")
        if etagDest == md5Src:
            is_same = True
        elif (len(etagDest.split("-")) == 2) and self.check_multipart_etag(
            local_file, etagDest
        ):
            # etag format suggests the file was uploaded as a multipart
            # which impacts how the etags are calculated
            is_same = True
        return is_same

    def check_multipart_etag(self, localFile, etagFromDest):
        """checks to see if the etag from S3 can be validated locally

        :param localFile: path to the local file
        :type localFile: str
        :param etagFromDest: the etag that was returned from s3
        :type etagFromDest: str
        :return: a boolean that tells us if the etag can be validated
        :rtype: bool
        """
        verifyEtag = CalcETags()
        return verifyEtag.etag_is_valid(localFile, etagFromDest)


class CalcETags(object):
    def __init__(self):
        self.defaultPartSize = 1048576

    def factor_of_1MB(self, filesize, num_parts):
        x = filesize / int(num_parts)
        y = x % self.defaultPartSize
        return int(x + self.defaultPartSize - y)

    def calc_etag(self, inputfile, partsize):
        md5_digests = []
        with open(inputfile, "rb") as f:
            for chunk in iter(lambda: f.read(partsize), b""):
                md5_digests.append(hashlib.md5(chunk).digest())
        return (
            hashlib.md5(b"".join(md5_digests)).hexdigest() + "-" + str(len(md5_digests))
        )

    def possible_partsizes(self, filesize, num_parts):
        return (
            lambda partsize: partsize < filesize
            and (float(filesize) / float(partsize)) <= num_parts
        )

    def etag_is_valid(self, inFilePath, s3eTag):
        LOGGER.debug(f"inFilePath: {inFilePath}, s3eTag: {s3eTag}")
        filesize = os.path.getsize(inFilePath)
        num_parts = int(s3eTag.split("-")[1])
        etag_is_valid = False
        # Default Partsizes Map: aws_cli/boto3, s3cmd
        partsizes = [
            8388608,
            15728640,
            self.factor_of_1MB(
                filesize, num_parts
            ),  # Used by many clients to upload large files
        ]

        for partsize in filter(self.possible_partsizes(filesize, num_parts), partsizes):
            calcETag = self.calc_etag(inFilePath, partsize)
            LOGGER.debug(f"etags froms3: {s3eTag}, calced: {calcETag}, {partsize}")

            if s3eTag == calcETag:
                LOGGER.debug("paths match")
                etag_is_valid = True
                break
        return etag_is_valid


class ObjectStoragePathLib:
    """class that wrap some functions to clean up file paths when working with
    object storage.
    """

    def __init__(
        self,
        obj_store_host=None,
        obj_store_user=None,
        obj_store_secret=None,
        obj_store_bucket=None,
    ):
        self.obj_store_host = obj_store_host
        self.obj_store_user = obj_store_user
        self.obj_store_secret = obj_store_secret
        self.obj_store_bucket = obj_store_bucket

        if self.obj_store_host is None:
            self.obj_store_host = constants.OBJ_STORE_HOST
        if self.obj_store_user is None:
            self.obj_store_user = constants.OBJ_STORE_USER
        if self.obj_store_secret is None:
            self.obj_store_secret = constants.OBJ_STORE_SECRET
        if self.obj_store_bucket is None:
            self.obj_store_bucket = constants.OBJ_STORE_BUCKET

    def remove_sr_root_dir(self, in_path, src_root_dir):
        """
        a utility method that will recieve a path, and remove a leading portion
        of that path.  For example if the input path was
        `/habs/guy/lafleur/points`

        and the source root directory src_root_dir was `/habs/guy`

        The output path would be `lafleur/points`

        :param in_path: the input path that is to have the root directory
            removed
        :type in_path: str
        :raises ValueError: raise if the the in_path is found to not be a
            subdirectory of the SRC_ROOT_DIR (env var)
        :return: modified src directory with the root potion removed
        :rtype: str
        """
        LOGGER.debug(f"in_path: {in_path}")
        rootPathObj = pathlib.PurePath(src_root_dir)
        in_pathObj = pathlib.PurePath(in_path)
        if rootPathObj not in in_pathObj.parents:
            msg = (
                f"expecting the root path {src_root_dir} to "
                + f"be part of the input path {in_path}"
            )
            LOGGER.error(msg)
            raise ValueError(msg)

        newPath = os.path.join(*in_pathObj.parts[len(rootPathObj.parts):])
        LOGGER.debug(f"newpath: {newPath}")
        return newPath

    def get_obj_store_path(
        self,
        src_path: str,
        ostore_path: str,
        src_root_dir: str,
        prepend_bucket: bool = True,
        include_leading_slash: bool = False,
    ):
        """Gets the source file path, calculates the destination path for
        use when referring to the destination location using the minio api.

        :param src_path: the source path referring to the file that is to be
            copied to object storage
        :param src_root_dir: the path to the original directory that is being
            copied, src_path is a sub dir of this path.  Example if src_path
            is /home/glafleur/players/roster/elite_habs2023.txt
            and the src_root_dir is /home/glafleur/players and the ostore_path
            is /backup/guy then the calculated ostore_path will be:
            /backup/guy/roster/elite_habs2023.txt
        :type src_path: str
        :param prepend_bucket: default is true, identifies if the name of the
            bucket should be the leading part of the destination path
        :type prepend_bucket: bool
        :param include_leading_slash: if the path should include a leading path
            delimiter character.  Example if true /guyLafleur/somedir
            would be the path, if set to false it would be guyLafleur/somedir
        :type include_leading_slash: bool
        """
        relativePath = self.remove_sr_root_dir(src_path, src_root_dir)
        if prepend_bucket:
            objStoreAbsPath = os.path.join(
                self.obj_store_bucket, ostore_path, relativePath
            )
        else:
            objStoreAbsPath = os.path.join(ostore_path, relativePath)
        if os.path.isdir(src_path):
            if objStoreAbsPath[-1] != os.path.sep:
                objStoreAbsPath = objStoreAbsPath + os.path.sep
        if include_leading_slash:
            if objStoreAbsPath[0] != os.path.sep:
                objStoreAbsPath = os.path.sep + objStoreAbsPath
        # object storage always uses posix / unix path delimiters
        if sys.platform == "win32":
            objStoreAbsPath = objStoreAbsPath.replace(os.path.sep, posixpath.sep)
        LOGGER.debug(f"object store absolute path: {objStoreAbsPath}")
        return objStoreAbsPath
