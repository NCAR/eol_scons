# -*- python -*-
import sys

def generate(env):
    env.Require('coin')
    env.Require(['qtgui', 'qtcore', 'qtwidgets', 'qtopengl', 'qwt'])
    env.AppendUnique(LIBS=['Quarter'])

    if sys.platform in ['linux', 'linux2']: 
        pass

    if sys.platform == 'darwin':
        pass

    if sys.platform == 'msys':
        env.AppendUnique(CXXFLAGS=["-DQUARTER_NOT_DLL"])
        env.Append(LIBS=["Quarter"])
        env.Append(LIBS=["Qt5Widgets"])
        env.Append(LIBS=["Qt5Gui"])
        env.Append(LIBS=["Qt5OpenGL"])

def exists(env):
    return True
