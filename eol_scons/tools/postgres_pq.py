# Postgres libpq 

import sys
import eol_scons.parseconfig as pc

def generate(env):
    # As of 2023, --cflags errors on darwin, did not follow up
    if sys.platform == 'darwin':
        pc.ParseConfig(env, 'pkg-config --libs libpq')
    else:
        if pc.CheckConfig(env, 'pkg-config --exists libpq'):
            pc.ParseConfig(env, 'pkg-config --cflags --libs libpq')
        else:
            env.AppendUnique(LIBS=['pq'])



def exists(env):
    return True

