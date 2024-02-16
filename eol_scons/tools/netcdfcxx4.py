import eol_scons.parseconfig as pc
import sys

def generate(env):
    """
    Tool for the netcdf-cxx4 library which replaces the legacy C++ API.
    """
    # name of library depends on which build tool was used to compile it (see
    # github issue: https://github.com/Unidata/netcdf-cxx4/issues/113). on mac,
    # the homebrew installation doesn't include a pkgconfig file, so stick with
    # the library name the homebrew installation uses (until we have a reason
    # to do otherwise). otherwise, try using pkg-config.
    if sys.platform == 'darwin':
        env.Append(LIBS=['netcdf-cxx4'])
    else:
        pc.ParseConfig(env,
                      'pkg-config --silence-errors --cflags --libs netcdf-cxx4')

    env.Require('netcdf')


def exists(env):
    return True
