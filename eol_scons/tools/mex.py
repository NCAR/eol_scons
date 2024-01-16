# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

# need this to determine the correct suffix
# 'env matlab -nodisplay -nojvm -r "mexext;quit" | grep mex'

import os
import SCons
from SCons.Builder import Builder
from subprocess import Popen, PIPE


_options = None


def findMex(env):
    global _options
    if not _options:
        _options = env.GlobalVariables()
        _options.Add('MEX_PATH',
                     'Path to mex, or else "mex" if unset.')

    _options.Update(env)

    # Short circuit the test if MEX_PATH is already set in the
    # run environment.
    if env.get('MEX_PATH'):
        return env['MEX_PATH']
    extra_paths = ['/usr/bin']
    if 'OPT_PREFIX' in env:
        extra_paths.append("%s/bin" % env['OPT_PREFIX'])
    opts = ['el4', 'el3', 'ws3', 'fc4', 'fc3', 'fc2']
    extra_paths.extend(["/net/opt_lnx/local_%s/bin" % o for o in opts])
    return env.WhereIs('mex', extra_paths)


def getMexPath(env):
    mex = findMex(env)
    if not mex:
        mex = "mex"
    return mex


def generate(env):
    cmd = ['matlab', '-nodisplay', '-nojvm']
    # invoke matlab
    p1 = Popen(cmd, stdin=PIPE, stdout=PIPE)
    os.write(p1.stdin.fileno(), "mexext\n")
    os.write(p1.stdin.fileno(), "quit\n")
    # now, invoke grep to retrieve the extension
    p2 = Popen(['grep', 'mex'], stdin=p1.stdout, stdout=PIPE)

    mexext = p2.communicate()[0][:-1]
    env['MEX_EXT'] = mexext

    bld = Builder(action='%s $SOURCE -o $TARGET' % getMexPath(env),
                  suffix=mexext)
    env['BUILDERS']['MEX'] = bld


def exists(env):
    if not findMex(env):
        SCons.Warnings.warn(SCons.Warnings.WarningOnByDefault,
                            "Could not find mex program.")
        return False
    return True
