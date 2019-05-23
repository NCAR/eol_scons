import sys

def generate(env):
    env.Tool('boost')
    if sys.platform != 'msys':
        env.AppendBoostLibrary('boost_date_time')

def exists(env):
    return True

