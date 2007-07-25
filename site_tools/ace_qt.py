
def generate(env):

  env.Append(LIBS=['ACE_QtReactor',])
  env.Require(['PKG_ACE', 'PKG_QT'])


def exists(env):
    return True

