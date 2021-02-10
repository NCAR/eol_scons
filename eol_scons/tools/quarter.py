# -*- python -*-

import sys

def generate(env):
    env.AppendUnique(LIBS=['Quarter'])
    env.Require('coin')
    env.Require(['qtgui', 'qtcore', 'qtwidgets', 'qtopengl', 'qwt'])

    if sys.platform == 'msys':
        env.AppendUnique(CXXFLAGS=["-DQUARTER_NOT_DLL"])
        env.Append(LIBS=["Qt5Widgets"])
        env.Append(LIBS=["Qt5Gui"])
        env.Append(LIBS=["Qt5OpenGL"])

def exists(env):
    return True
