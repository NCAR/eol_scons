# -*- python -*-

"""
Implement generic compiling profiles for gcc.

This also adds support for GCC-specific features like address and thread
sanitizing.  When the gcc tool is in use, the environment provides the
methods env.SanitizeThread() and env.SanitizeAddress() which add the right
compile and link flags.  Programs compiled with sanitization can then be
run and their output 'symbolized' using the AsanFilter wrapper.  For
example, the following runs the gtest executable and converts any asan
error output into source file and line numbers.

    env.SanitizeAddress()
    tests = env.Program('tests', ["test_something.cc"])
    env.Command('test', tests, env.AsanFilter("${SOURCE.abspath}"))

On Fedora systems, package libasan must be installed for GCC sanitized code
to link.  The asan_symbolize.py script is included directly because there
does not appear to be a Fedora package which provides it.
"""

import SCons.Tool
import SCons.Tool.gcc
import os



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

def AsanFilter(env, command):
    """
    Wrap a shell command so the output is symbolized with ASAN_FILTER.

    This works by setting pipefail in the shell and then piping the output
    of the command into the filter command.  It might be better to make
    this an actual Action implementation which filters the action output in
    the same way as LogAction in the testing.py tool.
    """
    return "set -o pipefail; %s 2>&1 | ${ASAN_FILTER}" % (command)

def generate(env):
    SCons.Tool.gcc.generate(env)
    env.AddMethod(Optimize)
    env.AddMethod(Debug)
    env.AddMethod(Warnings)
    env.AddMethod(Profile)
    env.AddMethod(SanitizeAddress)
    env.AddMethod(SanitizeThread)
    # There's no harm in always adding these to the construction
    # environment, whether sanitization will be used or not.  This way
    # environments can filter output from sanitized executables built in a
    # different environment.
    asan = os.path.join(os.path.dirname(__file__), "..", 'utils', 
                        'asan_symbolize.py')
    asan = os.path.normpath(asan)
    env.SetDefault(ASAN_SYMBOLIZE=asan)
    env.SetDefault(CXXFILT='c++filt')
    env.SetDefault(ASAN_FILTER="${ASAN_SYMBOLIZE} | ${CXXFILT}")
    env.AddMethod(AsanFilter)

def exists(env):
    return SCons.Tool.gcc.exists(env)
