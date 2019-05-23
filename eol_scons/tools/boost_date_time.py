
def generate(env):
    env.Tool('boost')
    env.AppendBoostLibrary('boost_date_time')

def exists(env):
    return True

