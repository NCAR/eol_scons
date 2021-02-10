# -*- python -*-

import os
import eol_scons.parseconfig as pc


def generate(env):
    if env['PLATFORM'] == 'msys':
        env.AppendUnique(CXXFLAGS=["-DCOIN_NOT_DLL"])
        pc.ParseConfig(env,
		'pkg-config --silence-errors --with-path=/usr/local/lib/pkgconfig --cflags --libs Coin')
    else:
        pc.ParseConfig(env,
		'pkg-config --silence-errors --cflags --libs Coin')

    if env['PLATFORM'] == 'posix':
        env.Append(LIBS=["GLU"])
        env.Append(LIBS=["dl"])
        env.Append(LIBS=["GL"])
        env.Append(LIBS=["X11"])

    if env['PLATFORM'] == 'msys':
        env.Append(LIBS=['opengl32'])
        env.Append(LIBS=['glu32'])
        env.Append(LIBS=['gdi32'])

    if env['PLATFORM'] == 'darwin':
        env.AppendUnique(FRAMEWORKS=['CoreFoundation'])
        env.AppendUnique(FRAMEWORKS=['CoreGraphics'])


    env.SetDefault(COIN_DOXREF='${COIN_DOXDIR}/coin.tag:${COIN_DOXDIR}')
    env.AppendDoxref('$COIN_DOXREF')


def exists(env):
    return True

