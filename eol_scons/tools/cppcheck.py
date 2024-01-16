# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
"""
cppcheck is a straightforward C++ code checker, with lots of checks for
bad code, poor style, and inefficient code.  It can accept typical C++
command-line flags like include paths and cpp definitions, so it is easiest
to just call it like a compiler.

It would be nice to add builders to run cppcheck on each source file
wherever a source file is added to a regular compile builder.  That would
require wrapping lots of methods like Object(), StaticObject(), Program(),
Library(), StaticLibrary(), and so on.

cppcheck can also check across entire all the source code in an executable
for unused functions and definitions.  However, with SCons, that would
require searching the dependency tree of an executable for all the source
files, and then passing all of those to cppcheck at once.  That sounds like
an attractive solution, but I don't know how to do it.  Maybe start with
the ninja.py tool and look for sources nodes with C++ filename extensions.
This would be nice approach in general for finding all the source files
which should be checked, and the command lines for them with the necessary
include and define options.

Instead of the more sophisticated options above, this first simple tool
attempt just rewrites the compile and related commands.  The compile
command runs cppcheck, and the link and archive commands are turned into
no-ops.  This can still cause errors from scons, if any of those outputs
are required for other targets or if scons notices they are not generated
as expected.  Also, it's not clear whether the check will be re-run on
files whose object files already exist.  So the recommended way to use this
tool is to first clean the source tree, and then run with the --keep-going
option:

    scons -c .
    scons buildmode=cppcheck -k

Of course the buildmode tool must be applied by the project.

Other build commands will be triggered for files which are dependencies of
the C++ objects, such as Qt moc and header compilers, only the C++ compile
and link commands will be modified.

Running cppcheck separately on every source file means all the warnings for
a single header file are repeated for each source file which includes it.
That annoyance could be fixed with one of the above approaches.

I found at least one other project on the web which has a scons target for
running cppcheck, but it just runs cppcheck on the top-level source
directory, allowing cppcheck to find all the source files itself.  This can
work well also, but it depends on how much a good analysis depends on
finding header files and using the right symbol definitions, and it means
all source will be analyzed, even unused source and autoconfigure source.
"""


def generate(env):
    env['CPPCHECKFLAGS'] = env.Split('--enable=all --template=gcc --quiet')
    # This is hardcoded to prevent cppcheck from testing both the defined
    # and undefined alternatives for Q_MOC_OUTPUT_REVISION, resulting in
    # warnings like "Header file does not include QObject".  In practice it
    # has a default in qobjectdefs.h for the particular version of Qt in
    # use, so that's the value cppcheck should use.  Of course this is for
    # Qt4, for Qt5 it needs to be 67.  It sort-of works to make sure
    # cppcheck finds and parses qobjectdefs.h in the standard header
    # locations, but parsing all the Qt header files also adds lots of
    # overhead, so this is perhaps more expedient and effective.
    env.Append(CPPCHECKFLAGS='-DQ_MOC_OUTPUT_REVISION=63')
    env.Append(CPPCHECKFLAGS='-UQT_BEGIN_HEADER')
    env.Append(CPPCHECKFLAGS='-UQT_BEGIN_NAMESPACE')
    env.Append(CPPCHECKFLAGS='-UQT_END_HEADER')
    env.Append(CPPCHECKFLAGS='-UQT_END_NAMESPACE')

    # env.Append(CPPCHECKFLAGS='--check-config')
    # env.Append(CPPCHECKFLAGS='-I/usr/include')

    # Put cppcheck flags last, in case it contains default header search
    # paths which should be searched last, same as compiler search paths.
    env['CXXCOM'] = 'cppcheck $_CCCOMCOM $SOURCES $CPPCHECKFLAGS'
    env['SHCXXCOM'] = 'cppcheck $_CCCOMCOM $SOURCES'
    env['LINKCOM'] = 'echo cppcheck not linking $TARGET'
    env['ARCOM'] = 'echo cppcheck not updating archive: $TARGET'
    env['RANLIBCOM'] = 'echo cppcheck not running $RANLIB $RANLIBFLAGS $TARGET'


def exists(env):
    return env.Detect('cppcheck')

