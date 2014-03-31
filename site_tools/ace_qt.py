
def generate(env):

  env.Append(LIBS=['ACE_QtReactor',])
  env.Require(['ace', 'qt'])

def exists(env):
    return True

