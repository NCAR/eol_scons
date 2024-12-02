# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
import os
import eol_scons.parseconfig as pc


def generate(env):
    if env['PLATFORM'] == 'msys':
# Latest msys2/mingw/ucrt provides coin & quarter.  Yeah!  So it's a DLL now.
# I'm just going to comment this out for now.	cjw 11/2024
#        env.AppendUnique(CXXFLAGS=["-DCOIN_NOT_DLL"])
        pc.ParseConfig(env,
		'pkg-config --silence-errors --with-path=/usr/local/lib/pkgconfig --cflags --libs Coin')
    else:
        pc.ParseConfig(env,
		'pkg-config --silence-errors --cflags --libs Coin')

# Redhat variants don't need this.  Leave it case Ubuntu or something needs it
#    if env['PLATFORM'] == 'posix':
#        env.Append(LIBS=["GLU"])
#        env.Append(LIBS=["GL"])
#        env.Append(LIBS=["X11"])

    # msys/ucrt coin pkg-config does not drag these in.  Do it manually here.
    if env['PLATFORM'] == 'msys':
        env.Append(LIBS=['opengl32'])
        env.Append(LIBS=['glu32'])
        env.Append(LIBS=['gdi32'])

    if env['PLATFORM'] == 'darwin':
        env.AppendUnique(FRAMEWORKS=['CoreFoundation'])
        env.AppendUnique(FRAMEWORKS=['CoreGraphics'])

    env.AppendUnique(DEPLOY_SHARED_LIBS=['Coin'])

    env.SetDefault(COIN_DOXREF='${COIN_DOXDIR}/coin.tag:${COIN_DOXDIR}')
    env.AppendDoxref('$COIN_DOXREF')


def exists(env):
    return True

