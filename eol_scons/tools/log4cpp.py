# Log4cpp

import eol_scons.parseconfig as pc

def generate(env):
    if pc.CheckConfig(env, 'pkg-config --exists log4cpp'):
        pc.ParseConfig(env, 'pkg-config --cflags --libs log4cpp')
    else:
        env.AppendUnique(LIBS=['log4cpp'])


def exists(env):
    return True

