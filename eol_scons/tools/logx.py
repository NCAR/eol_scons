

def generate(env):
    # include and lib paths are expected to already be part of the
    # default setup, either under the OPT_PREFIX or under the top
    # source directory.
    #env.Append(LIBPATH= ['#/logx',])
    #env.Append(LIBS=['logx',])
    env.AppendLibrary("logx")
    # By default expect logx to be built in the tree, but allow the doxref
    # to be overridden either way.
    env.SetDefault(LOGX_DOXREF="logx")
    env.AppendDoxref("$LOGX_DOXREF")
    env.Tool('log4cpp')

def exists(env):
    return True

