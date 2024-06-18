# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.


from pathlib import Path
from SCons.Variables import Variables
import eol_scons.parseconfig as pc
import sys
import os

_options: Variables

_options = None
_error_printed = False


def default_name() -> str:
    if sys.platform == 'darwin':
        return 'netcdf-cxx4'
    # default to package name on centos
    return 'netcdf_c++4'


def find_lib(nc4dir) -> tuple[Path, str]:
    """
    Find the library and return a (libdir, name) tuple.  When installed from
    source, the library can end up in a couple different places with a couple
    different names.
    """
    nc4dir = Path(nc4dir)
    search_paths = [(nc4dir / subdir, name) for subdir in ["lib64", "lib"]
                    for name in ["netcdf_c++4", "netcdf-cxx4"]]
    for pname in search_paths:
        (libdir, name) = pname
        if (libdir / f"lib{name}.so").exists():
            return pname
    # raising a StopError can prevent help usage, so just print a warning, but
    # only the first time.
    global _error_printed
    if not _error_printed:
        _error_printed = True
        print("netcdf-cxx4 library not found: %s" % (nc4dir))
    return search_paths[0]


def generate(env):
    """
    Tool for the netcdf-cxx4 library which replaces the legacy C++ API.
    """
    global _options
    if not _options:
        _options = env.GlobalVariables()
        _options.Add('NETCDFCXX4DIR', 'netcdf_c++4 installation path.', None)
    _options.Update(env)

    # the variable takes precedence if set
    nc4dir = env.get('NETCDFCXX4DIR')
    if nc4dir:
        libdir, name = find_lib(nc4dir)
        env.AppendUnique(LIBPATH=[str(libdir.resolve())])
        env.AppendUnique(CPPPATH=[os.path.join(nc4dir, 'include')])
        env.Append(LIBS=[name])

    # name of library depends on which build tool was used to compile it (see
    # github issue: https://github.com/Unidata/netcdf-cxx4/issues/113). on mac,
    # the homebrew installation doesn't include a pkgconfig file, so stick with
    # the library name the homebrew installation uses (until we have a reason
    # to do otherwise). otherwise, try using pkg-config.
    elif pc.ParseConfig(env,
                      'pkg-config --silence-errors --cflags --libs netcdf-cxx4'):
        pass
    else:
        # use default library name for current platform
        env.Append(LIBS=[default_name()])
    env.Require('netcdf')


def exists(env):
    return True
