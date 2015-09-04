
def generate(env):
    env.Tool('boost')
    env.AppendBoostLibrary('boost_system')


def exists(env):
    return True

