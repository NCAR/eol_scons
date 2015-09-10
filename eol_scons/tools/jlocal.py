"""
Setup paths to RAF headers and libraries.

This tool checks for a valid JLOCAL directory, specified either through the
OS environment or through a SCons variable, or by default /opt/local.  The
JLOCAL setting is valid if the path JLOCAL/include/raf exists.  In that
case, the include and lib paths are added automatically to the environment.

SConscript targets with JLOCAL dependencies can be compiled conditionally
by checking env.JLocalValid().
"""

import os
from SCons.Variables import PathVariable

_options = None

def generate(env):
    jlocal = '/opt/local'
    if os.environ.has_key('JLOCAL'):
        jlocal = os.environ['JLOCAL']

    global _options
    if not _options:
        _options = env.GlobalVariables()
        _options.AddVariables(
            PathVariable('JLOCAL',
                         'Path to RAF headers and libraries',
                         jlocal, PathVariable.PathAccept))
    _options.Update(env)
    env.AddMethod(_JLocalValid, "JLocalValid")
    if env.JLocalValid():
        env['JLOCALLIBDIR'] = "$JLOCAL/lib"
        env['JLOCALINCDIR'] = "$JLOCAL/include"
        env.Append(CPPPATH=['$JLOCALINCDIR'])
        env.Append(LIBPATH=['$JLOCALLIBDIR'])


def _JLocalValid(env):
    # Check if $JLOCAL/include/raf and $JLOCAL/lib exist.
    return bool((os.path.exists(os.path.join(env["JLOCAL"],'include','raf'))) 
                and
                (os.path.exists(os.path.join(env["JLOCAL"],'lib'))))


def exists(env):
    return True
