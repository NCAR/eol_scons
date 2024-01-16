# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
"""
Support for Pentek ReadyFlow.

The ReadyFlow library is built in x86/lib or x86_64/lib, using the
ReadyFlow Makefile, and installed in /usr/local as follows:

  cp ReadyFlow/1.0/include/* /usr/local/include/
  cp ReadyFlow/1.0/x86_64/include/* /usr/local/include/
  cp ReadyFlow/1.0/x86_64/lib/*7142* /usr/local/lib

A specific windriver library version must be identified via the
WINDRIVERVERSION variable.
"""


import os
import platform
import sys
import eol_scons
import SCons

# Readyflow is installed in /usr/local/ReadyFlow
installdir = '/usr/local/ReadyFlow'
libdir = os.path.join(installdir, 'lib')
includedir = os.path.join(installdir, 'include')

# Assume that ReadyFlow is installed under /usr/local/ReadyFlow
prefix = '/usr/local/ReadyFlow'
if not os.path.isdir(prefix):
    msg = "Unable to find ReadyFlow. Directory %s does not exist." % (prefix)
    raise SCons.Errors.StopError(msg)
    
# define the tool
def generate(env):

    options = env.GlobalVariables()
    options.AddVariables(('WINDRIVERVERSION', 'WinDriver version string.'))
    options.Update(env)
    
    # ReadyFlow requires LINUX to be defined
    env.AppendUnique(CPPDEFINES=['LINUX',])
    
    # We are using the ReadyFlow distribution 7142_428, so
    # OPT_428 must be defined.
    env.AppendUnique(CPPDEFINES=['OPT_428',])
    
    # Add include paths down in the ReadyFlow distribution
    env.AppendUnique(CPPPATH=[includedir])
    
    # This is a shared object library that contains the windriver license
    env.AppendUnique(LIBPATH=[libdir])
    env.AppendUnique(RPATH=[libdir])
    env.AppendLibrary('ptk7142_428')
    
    # This is the library containing the ReadyFlow API. We must
    # specify p7142_428.lib directly since it is does not follow
    # the standard library naming convention (lib*.a)
    p7142lib = env.File(os.path.join(libdir, 'p7142_428.lib'))
    env.Append(LIBS=[p7142lib])
    
    # add the windriver library, which ReadyFlow depends upon.
    if 'WINDRIVERVERSION' in env: 
        windriverlib = 'wdapi' + env['WINDRIVERVERSION']
    else:
        windriverlib = 'wdapi1150'
        print('WARNING: WINDRIVERVERSION was not specified; defaulting to version 1150.')
        print('         WinDriver library set to', windriverlib)
    env.AppendLibrary(windriverlib)
    
def exists(env):
    return True

