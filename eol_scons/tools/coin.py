# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

import eol_scons.parseconfig as pc


def generate(env):
    if env['PLATFORM'] in ['msys', 'win32'] and env['QT_VERSION'] == 5:
        env.AppendUnique(CXXFLAGS=["-DCOIN_NOT_DLL"])
        pc.ParseConfig(env,
            'pkg-config --silence-errors --with-path=/usr/local/lib/pkgconfig --cflags --libs Coin')
    else:
        pc.ParseConfig(env,
            'pkg-config --silence-errors --cflags --libs Coin')

    if env['PLATFORM'] == 'darwin':
        env.AppendUnique(FRAMEWORKS=['CoreFoundation'])
        env.AppendUnique(FRAMEWORKS=['CoreGraphics'])

    env.AppendUnique(DEPLOY_SHARED_LIBS=['Coin'])

    env.SetDefault(COIN_DOXREF='${COIN_DOXDIR}/coin.tag:${COIN_DOXDIR}')
    env.AppendDoxref('$COIN_DOXREF')


def exists(env):
    return True

