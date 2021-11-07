# Object Storage / S3 Utility Methods

<img src="https://lh3.googleusercontent.com/pw/AM-JKLV5unOdDuG_o7QwVYaiUCaFePQtcVWxPMJekkMNgQzVxKfkir0Akv9adldYQQTLVPW1W0O5Aov_Ep-v6HFcA6EwL3olmrkQW9Tm5k96K9Iv8uZAnrzc68vWIIs8gRt_wahaTmEv-XF1W9pxAygsesPHzw=w1292-h792-no?authuser=0" width="600">

Glueing together some object storage functionality into a
easy to use python library.

Intent is to bundle up commonly used functions into a single
library that can be imported into other projects.

# Installing

TODO: Fill this in

# Creating an NRObjStoreUtil Object by passing credentials

```
import NRObjStoreUtil
objstor = NRObjStoreUtil.ObjectStoreUtil(
    "name of object store host",
    "object store user / access",
    "object store secret",
    "object store bucket"
)
```

# Creating an NRObjStoreUtil Object using env vars

First populate the following environment variables:
* OBJ_STORE_BUCKET
* OBJ_STORE_SECRET
* OBJ_STORE_USER
* OBJ_STORE_HOST

Then create the NRObjStoreUtil object without args:
```
import NRObjStoreUtil
objstor = NRObjStoreUtil.ObjectStoreUtil()
```

# other methods summary:

getObject - used to copy an object from object store to filesystem
putObject - copy file from filesystem to object store.
listObjects - list objects in a bucket / directory
logObjectProperties - write object properties to the logs
getObjAsDict - takes any python object and converts it to a dict (debugging)
setPublicPermissions - makes an object public
setObjContentType - modify an objects content type
getForceDownloadHeaders - Gets headers that should be applied to an object to
                          force download when the object link is presented in
                          a browser.  Works in concert with getPresignedUrl()

