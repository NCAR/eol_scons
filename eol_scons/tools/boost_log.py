
# Start of a primitive tool to experiment with boost logging.  Lots of
# hard-coded decisions here.

def generate(env):
    env.Tool('boost')
    env.AppendBoostLibrary('boost_log_setup')
    env.AppendBoostLibrary('boost_log')
    env.AppendBoostLibrary('boost_thread')
    env.Append(LIBS=['pthread'])
    env.AppendUnique(CPPDEFINES=['BOOST_LOG_DYN_LINK'])

def exists(env):
    return True

