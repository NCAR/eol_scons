# Log4cpp

import sys
import eol_scons.parseconfig as pc

def generate(env):
    if pc.CheckConfig(env, 'pkg-config --exists log4cpp'):
        pc.ParseConfig(env, 'pkg-config --cflags --libs log4cpp')
    else:
        env.AppendUnique(LIBS=['log4cpp'])

    # Some issues with this and pthread.  aeros proper links, but aeros
    # 'scons test' does not.
    if sys.platform.startswith("linux"):
        env.AppendUnique(LIBS=['pthread'])

def exists(env):
    return True

