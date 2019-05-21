import sys

def generate(env):
    env.Tool('boost')
    # On mingw, boost_serialization is built into main libboost.
    if sys.platform != 'msys':
        env.AppendBoostLibrary('boost_serialization')

def exists(env):
    return True

