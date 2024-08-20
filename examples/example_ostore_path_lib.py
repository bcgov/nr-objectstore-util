# examples working with the ostore path lib
# ObjectStoragePathLib helps when you need to translate a source path to a
# destination path

import os
import sys

# lib path
libpath = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.append(libpath)
import NRUtil.NRObjStoreUtil


def simple_working_with_paths():
    local_file_path = './data/data2/junk.txt'
    # make the directory ./data in case it doesn't exist
    if not os.path.exists(os.path.dirname(local_file_path)):
        print(f'creating the dir {os.path.dirname(local_file_path)}')
        os.makedirs(os.path.dirname(local_file_path))

    # make the file if it doesn't exist
    if not os.path.exists(local_file_path):
        print(f'creating the file: {local_file_path}')
        fh = open(local_file_path, 'w')
        fh.close()

    # now translate the relative directory to an abolute directory
    # after done the path will get translated to something like
    # /home/glafleur/proj/ostore/data/data2/junk.txt
    local_file_abs_path = os.path.realpath(local_file_path)

    # a demo of how the util functionality can be used to take an absolute
    # path and truncate it up to the path you want
    # in this context take the absolute path:
    #     /home/glafleur/proj/ostore/data/data2/junk.txt
    # and convert to the string:
    #     data2/junk.txt
    ostr_path_util = NRUtil.NRObjStoreUtil.ObjectStoragePathLib()
    local_dir = './data/modis-terra/MOD10A1.061/2023.03.17/MOD10A1.A2023076.h11v03.061.2023078031324.hdf'
    data_dir = 'data'
    out_dir = ostr_path_util.remove_sr_root_dir(
        local_dir,
        data_dir
    )
    print(f"outdir = {out_dir}")


if __name__ == '__main__':
    simple_working_with_paths()