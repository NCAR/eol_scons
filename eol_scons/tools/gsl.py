# GNU Scientific Library.

import eol_scons.parseconfig as pc

def generate(env):
    pc.ParseConfig(env, 'pkg-config --cflags --libs gsl')


def exists(env):
    return True

