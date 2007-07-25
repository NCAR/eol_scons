import os

def generate(env):
        env.AppendUnique(CPPPATH=[os.path.join(env['OPT_PREFIX'],'include'),])
        if not env.has_key('HAS_OPT_INCLUDE'):
            env.Append(LIBPATH=[os.path.join(env['OPT_PREFIX'],'lib')])
            env['HAS_OPT_INCLUDE'] = 1
        env.Append(LIBS=['XmlRpc',])



def exists(env):
    return True

