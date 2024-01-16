# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
import sys

def generate(env):
    env.AppendUnique(DEPLOY_SHARED_LIBS=['Quarter'])
    env.AppendUnique(LIBS=['Quarter'])
    env.Require('coin')
    env.Require(['qtgui', 'qtcore', 'qtwidgets', 'qtopengl', 'qwt'])

    if sys.platform == 'cygwin':
        env.AppendUnique(CXXFLAGS=["-DQUARTER_NOT_DLL"])

def exists(env):
    return True
