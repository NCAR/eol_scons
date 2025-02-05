# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

import eol_scons.parseconfig as pc


def generate(env):
    if env['PLATFORM'] in ['msys', 'win32'] and env['QT_VERSION'] == 5:
        # this is path for manually installed Coin & Quarter
        env.AppendUnique(CXXFLAGS=["-DQUARTER_NOT_DLL"])
        pc.ParseConfig(env,
            'pkg-config --silence-errors --with-path=/usr/local/lib/pkgconfig --cflags --libs Quarter')
    else:
        pc.ParseConfig(env,
            'pkg-config --silence-errors --cflags --libs Quarter')

    env.AppendUnique(DEPLOY_SHARED_LIBS=['Quarter'])
    env.Require('coin')
#    env.Require(['qtgui', 'qtcore', 'qtwidgets', 'qtopengl', 'qwt'])

def exists(env):
    return True
