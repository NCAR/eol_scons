
import SCons.Tool
import SCons.Tool.gcc

def Debug(env):
    env.Append(CCFLAGS=['-g'])
    return env

def Warnings(env):
    env.Append(CCFLAGS=['-Wall'])
    if env.has_key('NOUNUSED'):
        env.Append (CCFLAGS=['-Wno-unused'])
    return env

def Optimize(env):
    env.Append(CCFLAGS=['-O2'])
    return env

def Profile(env):
    env.Append(CCFLAGS=['-pg'])
    env.Append(LINKFLAGS=['-pg'])
    env.Append(SHLINKFLAGS=['-pg'])
    return env

def generate(env):
    SCons.Tool.gcc.generate(env)
    env.Optimize = Optimize
    env.Debug = Debug
    env.Warnings = Warnings
    env.Profile = Profile

def exists(env):
    return SCons.Tool.gcc.exists(env)
