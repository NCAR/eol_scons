

def generate(env):
    # include and lib paths are expected to already be part of the
    # default setup, either under the OPT_PREFIX or under the top
    # source directory.
    #env.Append(LIBPATH= ['#/logx',])
    #env.Append(LIBS=['logx',])
    env.AppendLibrary ("logx")
    if env.GetGlobalTarget("liblogx"):
	env.AppendDoxref("logx")
    else:
	env.AppendDoxref("logx:/net/www/software/raddx/apidocs/logx/html")
    # env.ExtraSources("liblogx")
    env.Tool ('log4cpp')

def exists(env):
    return True

