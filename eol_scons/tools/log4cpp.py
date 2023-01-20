# Log4cpp

import eol_scons.parseconfig as pc

def generate(env):
    pc.ParseConfig(env, 'pkg-config --cflags --libs log4cpp')


def exists(env):
    return True

