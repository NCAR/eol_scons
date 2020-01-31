# -*- python -*-

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

from eol_scons.ldd import ldd
from eol_scons.parseconfig import RunConfig

def _find_boost(env, libpython):
    """
    Find all the boost_python libraries, then pick out the one which
    depends on the python library passed in libpython.  There's a big
    assumption here that the first one found will be correct.  Really this
    should check in order the standard library paths and then LIBPATH.
    """
    libpaths = env.Glob("/usr/lib*/libboost_python*.so")
    for lib in libpaths:
        deps = ldd(lib, env)
        plibs = {k:v for k,v in deps.items() if 'python' in k}
        for k,v in plibs.items():
            if k == libpython:
                return lib


def generate(env):

    pconfig = env.WhereIs("python3-config") or env.WhereIs("python-config")
    if not pconfig:
        msg = "boost_python requires python3-config or python-config."
        raise SCons.Errors.StopError(msg)

    env.MergeFlags('!%s --includes' % (pconfig))

    plibs = RunConfig(env, pconfig + ' --libs')
    rx = re.search(r"-l(python[^ ]*) ", plibs)
    if not rx:
        msg = ("boost_python: could not parse python library name from "
               "%s output: %s" % (pconfig + ' --libs', plibs))
        raise SCons.Errors.StopError(msg)
    plibname = rx.group(1)
    env.LogDebug("found python shared library name: %s" % (plibname))
    env.LogDebug("looking for a boost library which depends on %s" % (plibname))
    blib = _find_boost(env, plibname)
    if not blib:
        msg = ("boost_python: could not find boost_python library which "
               "depends on: %s" % (plibname))
        raise SCons.Errors.StopError(msg)

    env.LogDebug("found boost library: %s" % (blib))
    env.Append(LIBS=[blib])
    env.MergeFlags('!%s --ldflags' % (pconfig))


def exists(env):
    return True


if __name__ == "__main__":
    from SCons.Environment import Environment
    import eol_scons
    eol_scons.debug.SetDebug(True)
    env = Environment(tools=['default'])
    generate(env)

