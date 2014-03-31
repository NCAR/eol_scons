
def generate(env):
    env.Tool('boost')
    env.AppendBoostLibrary('boost_filesystem')

def exists(env):
    return True

