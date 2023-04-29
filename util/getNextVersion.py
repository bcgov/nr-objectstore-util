import distutils.version
import os
import pprint
import sys

import packaging.version
import requests

# the version that comes from hatch.  What is currently configured
current_local_ver = sys.argv[1]
pypi_ver = None

# tet the versions from pypi
url = 'https://pypi.org/pypi/nr-objstore-util/json'
r = requests.get(url)
data = r.json()

# iterate the pypi versions to retrieve the most recent
for release in data['releases'].keys():
    #print(f'release: {release}')
    if pypi_ver is None:
        pypi_ver = release
    elif packaging.version.parse(release) >= packaging.version.parse(pypi_ver):
        pypi_ver = release

# if current local is ahead of pypi then use current local
if packaging.version.parse(pypi_ver) < packaging.version.parse(current_local_ver):
    next_ver = current_local_ver
else:
    # if current local is behind pypi then increment the latest pypi version
    # and use it
    nxt_ver_list = pypi_ver.split('.')
    nxt_ver_list[1] = str(int(nxt_ver_list[1]) + 1)
    next_ver = '.'.join(nxt_ver_list)

# output the current local
sys.stdout.write(next_ver + '\n')
