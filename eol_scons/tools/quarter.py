# -*- python -*-

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
