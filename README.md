[![Lifecycle:Maturing](https://img.shields.io/badge/Lifecycle-Maturing-007EC6)](<Redirect-URL>)

# Object Storage / S3 Utility Methods

<img src="https://lh3.googleusercontent.com/pw/AM-JKLV5unOdDuG_o7QwVYaiUCaFePQtcVWxPMJekkMNgQzVxKfkir0Akv9adldYQQTLVPW1W0O5Aov_Ep-v6HFcA6EwL3olmrkQW9Tm5k96K9Iv8uZAnrzc68vWIIs8gRt_wahaTmEv-XF1W9pxAygsesPHzw=w1292-h792-no?authuser=0" width="600">

Glueing together some object storage functionality into a
easy to use python library.

Intent is to bundle up commonly used functions into a single
library that can be imported into other projects.

# Installing

`pip install nr_objstore_util`

# Creating an NRObjStoreUtil Object by passing credentials

```python
import NRUtil.NRObjStoreUtil as NRObjStoreUtil
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

```bash
export OBJ_STORE_BUCKET=bucket_name
export OBJ_STORE_SECRET=sdf3jkllvjiojl;a4sf892ikfjovj
export OBJ_STORE_USER=ostoreuser
export OBJ_STORE_HOST=nrs.objectstore.gov.bc.ca
```


Then create the NRObjStoreUtil object without args:
```python
import NRUtil.NRObjStoreUtil as NRObjStoreUtil
objstor = NRObjStoreUtil.ObjectStoreUtil()
```

# Examples

... see the examples folder for examples

