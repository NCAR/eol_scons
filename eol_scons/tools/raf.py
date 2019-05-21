# -*- python -*-

def generate(env):
    env.Append(CPPPATH=['.'])
    env.Append(LIBPATH=['#/raf'])
    env.AppendLibrary('raf')

def exists(env):
    return True
