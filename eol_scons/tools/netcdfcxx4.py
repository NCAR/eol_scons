import eol_scons.parseconfig as pc
import sys
import os

_options = None

def generate(env):
    """
    Tool for the netcdf-cxx4 library which replaces the legacy C++ API.
    """
    global _options
    if not _options:
        _options = env.GlobalVariables()
        _options.Add('NETCDFCXX4DIR', 'netcdf_c++4 installation path.', None)
    _options.Update(env)

    if 'NETCDFCXX4DIR' in env:
        nc4dir = env['NETCDFCXX4DIR']
        env.AppendUnique(LIBPATH=[os.path.join(nc4dir, 'lib')])
        env.AppendUnique(CPPPATH=[os.path.join(nc4dir, 'include')])

    # name of library depends on which build tool was used to compile it (see
    # github issue: https://github.com/Unidata/netcdf-cxx4/issues/113). on mac,
    # the homebrew installation doesn't include a pkgconfig file, so stick with
    # the library name the homebrew installation uses (until we have a reason
    # to do otherwise). otherwise, try using pkg-config.
    if sys.platform == 'darwin':
        env.Append(LIBS=['netcdf-cxx4'])
    elif pc.ParseConfig(env,
                      'pkg-config --silence-errors --cflags --libs netcdf-cxx4'):
        pass
    else:
        # default to package name on centos
        env.Append(LIBS=['netcdf_c++4'])
    env.Require('netcdf')


def exists(env):
    return True
