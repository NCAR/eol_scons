import os

def generate(env):
#	env.AppendUnique(CPPPATH=[os.path.join(env['OPT_PREFIX'],'include'),])
#	env.AppendUnique(LIBPATH=[os.path.join(env['OPT_PREFIX'],'lib')])
        env.Append(LIBS=['bz2',])
        
        

def exists(env):
    return True

