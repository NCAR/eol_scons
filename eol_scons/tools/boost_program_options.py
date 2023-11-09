
def generate(env):
    env.Tool('boost')
    env.AppendBoostLibrary('boost_program_options')


def exists(env):
    return True
