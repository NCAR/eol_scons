# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
"""
Tool to setup Homebrew for MacOS.
"""


import subprocess


def generate(env):
    if env['PLATFORM'] != 'darwin':
      return

    brewPrefix = subprocess.run(['brew', '--prefix'], capture_output=True, text=True).stdout.strip()

    env['BREW_PREFIX'] = brewPrefix
    env.PrependENVPath('PATH', brewPrefix + '/bin')
    env.AppendUnique(FRAMEWORKPATH=[brewPrefix + '/Frameworks',])


def exists(env):
    return True
