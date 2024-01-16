# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
"""
To build against boost python, we need to know two things:

 1. Where the python headers are installed to add the directories to the
    include path.

 2. Which version of python that is, so we can add the right version of the
    boost-python library to LIBS, for those systems with different
    boost-python libraries for python 2 and 3.  Fedora can have both
    libboost_python27 and libboost_python37, while RHEL7 has just
    libboost_python and python-config.

If we can find python3-config, then use that, and if not, use the 'system
default' python-config.  From the python-config libs output, figure out
which python library is being used, then we for the right
libboost_python*.so which depends on that same python library.
"""

import re

import SCons
from SCons.Script import FindPathDirs

from eol_scons.ldd import ldd
from eol_scons.parseconfig import RunConfig

_variables = None


def _find_boost(env, libpython):
    """
    Find all the boost_python libraries, then pick out the one which
    depends on the python library passed in libpython.  There's a big
    assumption here that the first one found will be correct.  Really this
    should check in order the standard library paths and then LIBPATH.  The
    point is that if the python library has a version in it's name, like
    libpython3.6m, then this will find the boost_python library file which
    has that python library name as a dynamic dependency.  Otherwise,
    default to the first one found, in case the LIBPATH has been set to
    find the compatible libraries first.  This can still return None if
    there are no files in the library search path matching
    libboost_python*.
    """
    libdirs = list(FindPathDirs('LIBPATH')(env))
    libdirs.extend(env.Dir(['/usr/lib64', '/usr/lib']))
    libpaths = []
    for libdir in libdirs:
        libpaths.extend(env.Glob(libdir.abspath + "/libboost_python*.so"))
    env.LogDebug("scanning boost_python libs: %s" %
                 (",".join([str(lp) for lp in libpaths])))
    firstlib = None
    for lib in libpaths:
        if firstlib is None:
            firstlib = lib
        deps = ldd(lib, env)
        plibs = {k: v for k, v in deps.items() if 'python' in k}
        for k, v in plibs.items():
            if k == libpython:
                return lib
    # If we get here, then no boost_python library was found with the right
    # python dynamic dependency, so just return the first one found, on the
    # assumption it's the right one because it appears first in the
    # LIBPATH.  It might make sense to confirm the library is in the same
    # directory as the first python library, but not until proven
    # necessary.
    env.LogDebug("could not find boost_python library which depends on %s, "
                 "using first boost_python found: %s" % (libpython, firstlib))
    return firstlib


def generate(env):
    require_plib = False
    global _variables
    if _variables is None:
        _variables = env.GlobalVariables()
        _variables.Add('PYTHON_CONFIG', """
Path to the python config script, such as python-config or python3-config.
The script is called to add the include and link flags for compiling against
that python library.  python-config is the default.""".strip())

    _variables.Update(env)
    pconfig = env.get('PYTHON_CONFIG', 'python-config')
    # WhereIs() will make sure an absolute path exists or else a relative
    # path is on the PATH.
    pconfig = env.WhereIs(pconfig)
    if not pconfig:
        msg = str("boost_python requires python-config, or "
                  "set it with PYTHON_CONFIG variable.")
        raise SCons.Errors.StopError(msg)
    env.LogDebug("using python config: %s" % (pconfig))

    env.MergeFlags('!%s --includes' % (pconfig))

    plibs = RunConfig(env, pconfig + ' --libs')
    rx = re.search(r"-l(python\S*)", plibs)
    plibname = None
    if rx:
        plibname = rx.group(1)
    else:
        msg = ("boost_python: could not parse python library name from "
               "%s output: %s" % (pconfig + ' --libs', plibs))
        env.LogDebug(msg)
        if require_plib:
            raise SCons.Errors.StopError(msg)
    # Get flags to find the python library, especially LIBPATH so
    # _find_boost can look in the right lib directories.
    ldflags = RunConfig(env, pconfig + ' --ldflags')
    env.LogDebug("using ldflags: %s" % (ldflags))
    # If there is no python lib in the config output, then assume the right
    # libboost_python will be found on the LIBPATH set by python-config.
    # This accommodates conda environments where python3-config does not
    # list a python library name, but the libboost_python libraries have
    # the python version as a suffix even though without naming the shared
    # python library as a dynamic dependency.
    blib = 'boost_python'
    if plibname:
        env.LogDebug("python library name extracted from python config: %s" %
                     (plibname))
    else:
        plibname = "python"
        env.LogDebug("using default python library name: %s" % (plibname))

    env.LogDebug("looking for a boost library which depends on %s" %
                 (plibname))
    clone = env.Clone()
    clone.MergeFlags(ldflags)
    blib = _find_boost(clone, plibname)
    if not blib:
        blib = "boost_python"
        print("boost_python: could not find specific boost_python library "
              "to match python library %s, using default: %s" %
              (plibname, blib))
    else:
        print("using boost_python library: %s" % (blib))

    # Add the python library dependencies after the boost_python library
    # which depends on them.
    env.Append(LIBS=[blib])
    env.MergeFlags(ldflags)


def exists(env):
    return True


if __name__ == "__main__":
    from SCons.Environment import Environment
    import eol_scons
    eol_scons.debug.SetDebug(True)
    env = Environment(tools=['default'])
    generate(env)
