# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

import subprocess as sp
import re

def ldd(node, env, names=None):
    """
    Return a map with the name of each shared library dependency and its
    resolved location.  If a list of names is specified, then only include
    the libraries matching those names.  Node is a scons file node for any
    shared executable, including shared libraries.  Any matched
    dependencies will themselves be searched for dependencies.
    """
    libraries = {}
    # Run ldd on the program
    lddcmd = ["ldd", node.get_abspath()]
    env.LogDebug(lddcmd)
    lddprocess = sp.Popen(lddcmd, stdout=sp.PIPE)
    lddout = lddprocess.communicate()[0].decode()
    env.LogDebug(lddout)
    for line in lddout.splitlines():
        # add second group to regex to exclude version number from libname
        match = re.search(r"lib(.+?)(-[\d.]*)?\.so.*=> (.+) \(.*\)", line)
        if match:
            libname = match.group(1)
            lib = env.File(match.group(3))
            if ((names is None or libname in names) and
                libname not in libraries):
                env.LogDebug("Found %s" % (str(lib)))
                libraries[libname] = lib
                libraries.update (ldd(lib, env, names))
    return libraries


def _dump_libs(libs):
    print("\n".join(["%s : %s" % (name, lib.get_abspath())
                     for name, lib in libs.items()]))


if __name__ == "__main__":
    from SCons.Environment import Environment
    import eol_scons
    eol_scons.debug.SetDebug(True)
    env = Environment(tools=['default'])
    libs = ldd(env.File("/usr/lib64/libX11.so"), env)
    _dump_libs(libs)
    libs = ldd(env.File("/usr/lib64/libboost_python27.so"), env)
    _dump_libs({ k:v for k,v in libs.items() if 'python' in k })
    libs = ldd(env.File("/usr/lib64/libboost_python37.so"), env)
    _dump_libs({ k:v for k,v in libs.items() if 'python' in k })
