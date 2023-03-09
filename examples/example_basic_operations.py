import NRUtil.NRObjStoreUtil

"""
assuming the following env vars have been set:

export OBJ_STORE_BUCKET=bucket_name
export OBJ_STORE_SECRET=sdf3jkllvjiojl;a4sf892ikfjovj
export OBJ_STORE_USER=ostoreuser
export OBJ_STORE_HOST=nrs.objectstore.gov.bc.ca
"""

ostore = NRUtil.NRObjStoreUtil.ObjectStoreUtil()

# copy a local file called junk.txt to object storage
# -- create the file
local_file = "junk.txt"
with open(local_file, 'w') as fh:
    fh.write('example example example\n')

# copies from local junk.txt to remote on object store /junk/junky.txt
dest_file_path = '/junk/junky.txt'
ostore.put_object(local_path=local_file, ostore_path=dest_file_path)

# get a presigned url that expires in 60 seconds
pre_sign_url = ostore.get_presigned_url(object_name=dest_file_path, expires=60)
print(f"pre_sign_url: {pre_sign_url}")

# make the object public, ie access without a url
ostore.set_public_permissions(object_name=dest_file_path)

# delete the remote object
ostore.delete_remote_file(dest_file_path)
