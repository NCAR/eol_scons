# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
"""
Tool to determine Mac prefix.  Test for homebrew, then MacPorts.

"""


import subprocess
import sys


def generate(env):
    if env['PLATFORM'] != 'darwin':
      return

    try:
      macPrefix = subprocess.run(['brew', '--prefix'], capture_output=True, text=True).stdout.strip()
    except FileNotFoundError:
      try:
        macPrefix = subprocess.run(['port'], capture_output=True, text=True).stdout.strip()
        macPrefix='/opt/local'
      except FileNotFoundError:
        print('macprefix: no brew or port command avaialble, unclear install prefix.')
        sys.exit()


    env['MACOS_PREFIX'] = macPrefix
    env.PrependENVPath('PATH', macPrefix + '/bin')

    # Since a number of packages didn't have a pkg-config file under homebrew
    # only (e.g. xerces-c and netcdf-cxx4), at least cover the default location
    # Only really needed for ARM64
    env.Prepend(CPPPATH=[macPrefix + '/include'])
    env.Prepend(LIBPATH=[macPrefix + '/lib']) 

    env.AppendUnique(FRAMEWORKPATH=[macPrefix + '/Frameworks',])


def exists(env):
    return True
