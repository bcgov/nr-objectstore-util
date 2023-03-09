# passing params manually in

import NRUtil.NRObjStoreUtil as NRObjStoreUtil

objstor = NRObjStoreUtil.ObjectStoreUtil()
# inDir is  the directory to be listed
objList = objstor.listObjects(inDir='bsg/')
# link expire in seconds
expires = 60 * 60 * 24

# links are written to this file
linksFile = 'links.txt'

objstor.createBotoClient()
with open(linksFile, 'w') as fh:
    for obj in objList:
        if not obj.is_dir:
            # getting headers that force download of the object
            headers = objstor.getForceDownloadHeaders(obj.object_name)
            # now get the presign url
            url = objstor.getPresignedUrl(obj.object_name, expires=expires,
                                          headers=headers)
            # write the url to the link file
            fh.write(url + '\n')
