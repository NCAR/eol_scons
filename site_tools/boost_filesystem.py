import os,os.path, sys
import SCons

def generate(env):
	env.Append(LIBS=['boost_filesystem',])
	env.AppendUnique(LIBPATH=[os.path.join(env['OPT_PREFIX'],'lib'),])


def exists(env):
    return True

