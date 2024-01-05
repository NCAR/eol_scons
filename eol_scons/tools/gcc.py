# -*- python -*-

"""
Implement generic compiling profiles for gcc.

This also adds support for GCC-specific features like address and thread
sanitizing.  When the gcc tool is in use, the environment provides the methods
env.SanitizeThread() and env.SanitizeAddress() to add the right compile and
link flags.  On Fedora systems, package libasan must be installed for GCC
sanitized code to link.  As of at least gcc 5.x, sanitized messages are
already translated into demangled symbols, so the output does not need to be
passed through the asan_symbolize.py script and c++filt.  Any calls to
AsanFilter() can be replaced with just the same command.  The
SanitizeSupported() method has been removed also, since afaik it was never
used, and the same can be achieved by just checking for the existence of the
required method, eg, hasattr(env, 'SanitizeAddress').
"""

import SCons.Tool
import SCons.Tool.gcc


def Debug(env):
    env.Append(CCFLAGS=['-g'])
    return env


def Warnings(env):
    env.Append(CCFLAGS=['-Wall'])
    if 'NOUNUSED' in env:
        env.Append(CCFLAGS=['-Wno-unused'])
    return env


def Optimize(env):
    env.Append(CCFLAGS=['-O2'])
    return env


def Profile(env):
    env.Append(CCFLAGS=['-pg'])
    env.Append(LINKFLAGS=['-pg'])
    env.Append(SHLINKFLAGS=['-pg'])
    return env


def SanitizeAddress(env):
    env.Append(CCFLAGS=['-fsanitize=address', '-fno-omit-frame-pointer'])
    env.Append(LINKFLAGS=['-fsanitize=address'])
    env.Append(SHLINKFLAGS=['-fsanitize=address'])
    return env


def SanitizeThread(env):
    env.Append(CCFLAGS=['-fsanitize=thread', '-fno-omit-frame-pointer'])
    env.Append(LINKFLAGS=['-fsanitize=thread'])
    env.Append(SHLINKFLAGS=['-fsanitize=thread'])
    return env


def generate(env):
    SCons.Tool.gcc.generate(env)
    env.AddMethod(Optimize)
    env.AddMethod(Debug)
    env.AddMethod(Warnings)
    env.AddMethod(Profile)
    env.AddMethod(SanitizeAddress)
    env.AddMethod(SanitizeThread)


def exists(env):
    return SCons.Tool.gcc.exists(env)
