# Simple scons tool to find a valgrind executable and set the VALGRIND_PATH
# construction variable accordingly.  The value will also be available in
# the runtime environment, such as for test scripts executed by scons.

import os
import re
import SCons
from SCons.Builder import Builder
from SCons.Action import Action


class ValgrindWarning(SCons.Warnings.Warning):
    pass

_options = None

def findValgrind(env):
    global _options
    if not _options:
        _options = env.GlobalOptions()
        _options.Add('VALGRIND_PATH',
                     'Path to valgrind, or else "valgrind" if unset.')

    _options.Update(env)

    # Short circuit the test if VALGRIND_PATH is already set in the
    # run environment.
    if env.get('VALGRIND_PATH'):
        return env['VALGRIND_PATH']
    extra_paths = [ '/usr/bin' ]
    if env.has_key('OPT_PREFIX'):
        extra_paths.append("%s/bin" % env['OPT_PREFIX'])
    opts = ['el4','el3','ws3','fc4','fc3','fc2']
    extra_paths.extend([ "/net/opt_lnx/local_%s/bin" % o for o in opts])
    return env.WhereIs('valgrind', extra_paths)

def getValgrindPath(env):
    valgrind = findValgrind(env)
    if not valgrind:
        valgrind = "valgrind"
    return valgrind


def generate(env):
    valgrind = getValgrindPath(env)
    env['ENV']['VALGRIND_PATH'] = valgrind
    env['VALGRIND_PATH'] = valgrind


def exists(env):
    if not findValgrind(env):
        SCons.Warnings.warn(ValgrindWarning,
                            "Could not find valgrind program.")
        return False
    return True
