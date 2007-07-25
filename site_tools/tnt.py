import os

def generate(env):
        env.AppendUnique(CPPPATH=[os.path.join(env['OPT_PREFIX'],'include'),])



def exists(env):
    return True

