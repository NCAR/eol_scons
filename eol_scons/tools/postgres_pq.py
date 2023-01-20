# GNU Scientific Library.

import eol_scons.parseconfig as pc

def generate(env):
    if sys.platform == 'darwin':
        pc.ParseConfig(env, 'pkg-config --libs libpq')
    else:
        pc.ParseConfig(env, 'pkg-config --cflags --libs libpq')



def exists(env):
    return True

