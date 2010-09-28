import os,os.path, sys
import SCons

def generate(env):
    env.Append(LIBS=['boost_system',])
    libpath = os.path.abspath(os.path.join(env['OPT_PREFIX'],'lib'))
    env.AppendUnique(LIBPATH=[libpath])


def exists(env):
    return True

