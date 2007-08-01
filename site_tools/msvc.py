
import SCons.Tool
import SCons.Tool.msvc

def Debug(env):
    env.Append(CCFLAGS='/Zi')
    return env

def Warnings(env):
    # env.Append(CCFLAGS='/Wall')
    env.Append(CCFLAGS='/W2')
    if env.has_key('NOUNUSED'):
        pass
    return env

def Optimize(env):
    env.Append(CCFLAGS='/O2')
    return env

def Profile(env):
    return env

def generate(env):
    SCons.Tool.msvc.generate(env)
    env.Optimize = Optimize
    env.Debug = Debug
    env.Warnings = Warnings
    env.Profile = Profile

def exists(env):
    return SCons.Tool.msvc.exists(env)
