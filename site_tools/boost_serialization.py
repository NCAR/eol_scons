
def generate(env):
    env.Tool('boost')
    env.AppendBoostLibrary('boost_serialization')

def exists(env):
    return True

