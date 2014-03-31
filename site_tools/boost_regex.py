
def generate(env):
    env.Tool('boost')
    env.AppendBoostLibrary('boost_regex')

def exists(env):
    return True

