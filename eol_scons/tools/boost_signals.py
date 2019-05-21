
def generate(env):
    env.Tool('boost')
    env.AppendBoostLibrary('boost_signals')


def exists(env):
    return True

