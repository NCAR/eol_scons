import os,os.path, sys
import SCons

def generate(env):
	print 'foray_utility - generate called'
	env.Append(LIBS=['forayutil',])

	libpath = os.path.join(env['OPT_PREFIX'], 'foray', 'lib')
	env.AppendUnique(LIBPATH=[libpath,])

	inc_path = os.path.join(env['OPT_PREFIX'], 'foray', 'include')
	env.AppendUnique(CPPPATH=[inc_path,])

def exists(env):
    return True

