# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
import os
import SCons.Util

_options = None

liblibs = ['boost_unit_test_framework',
           'boost_prg_exec_monitor',
           'boost_test_exec_monitor',
           'boost_wave']


def boost_libflags(env):
    newlibs = []
    for lib in env['LIBS']:
        if SCons.Util.is_String(lib) and \
                lib.startswith("boost_") and \
                not lib.endswith("$BOOST_LIBRARY_SUFFIX"):
            if env['PLATFORM'] == 'msys' and lib in liblibs:
                lib = 'lib'+lib
            newlibs.append(lib+"$BOOST_LIBRARY_SUFFIX")
        else:
            newlibs.append(lib)
    env['LIBS'] = newlibs
    result = env.subst(env['_boost_save_libflags'])
    return result


def _append_boost_library(env, libname):
    if env['PLATFORM'] != 'darwin' and env['PLATFORM'] != 'msys':
        env.Append(LIBS=[libname])
    else:
        env.Append(LIBS=[libname + "-mt"])


def boost_version(env):
    """
    The detection of the boost version depends on an unconventional use of
    compiler options to query BOOST_VERSION from the boost/version.hpp header
    file.
    """
    version = env.get('BOOST_VERSION')
    if not version:
        # This command is essentially a copy of CXXCOM, except it cannot
        # contain the CXXFLAGS.  gcc thinks it is compiling C code since there
        # is no source file extension to key off, so it complains that
        # C++-specific flags like c++11 are invalid.  The _CCCOMCOM is
        # important because it is the CPPPATH expansion.
        #
        cppsource = """
#include <boost/version.hpp>
BOOST_VERSION
"""
        command = str('$CXX -E $CCFLAGS $_CCCOMCOM -o - -')
        # subst_list returns a list of CmdStringHolder instances inside a list,
        # so convert it to a simple argument list of strings.
        cmd = [str(arg) for arg in env.subst_list(command)[0]]
        import subprocess as sp
        env.LogDebug("boost_version(): %s" % (cmd))
        subp = sp.Popen(cmd, shell=False, stdin=sp.PIPE, stdout=sp.PIPE,
                        universal_newlines=True)
        output = subp.communicate(cppsource)[0]
        if subp.returncode:
            print("boost_version() failed: %s" % (cmd))
            env.Exit(1)
        version = output.splitlines()[-1]
        if version:
            version = int(version)
            env['BOOST_VERSION'] = version
        else:
            version = None
        env.PrintProgress("BOOST_VERSION=%s" % (version))
    return version


def generate(env):
    if env.get('BOOST_TOOL_APPLIED'):
        return
    env['BOOST_TOOL_APPLIED'] = True
    global _options
    if not _options:
        _options = env.GlobalVariables()
        _options.Add('BOOST_DIR',
                     """Set the BOOST installation directory.  Otherwise the default
 is to use the system location.  Specify BOOST_DIR=/usr to force
 the system installation even when a boost directory is found in
 OPT_PREFIX.""",
                     env.FindPackagePath('BOOST_DIR', '$OPT_PREFIX/boost*'))
    _options.Update(env)
    # env.Append(DEPLOY_SHARED_LIBS=['boost_date_time'])
    # env.Append(DEPLOY_SHARED_LIBS=['boost_serialization'])
    if 'BOOST_LIBRARY_SUFFIX' not in env:
        # We don't have any platform specific suffix at this time.
        env['BOOST_LIBRARY_SUFFIX'] = ''

    if 'BOOST_DIR' in env:
        bdir = env['BOOST_DIR']
        if bdir and bdir != "/usr" and bdir != "":
            env.Append(CPPPATH=[os.path.join(bdir, "include")])
            # Windows installs don't have a separate include directory.
            env.Append(CPPPATH=[os.path.join(bdir)])
            env.AppendUnique(LIBPATH=[os.path.join(bdir, "lib")])
            env.AppendUnique(RPATH=[os.path.join(bdir, "lib")])

    # Override the _LIBFLAGS variable so we can append the suffix for
    # boost libraries.
    if '_boost_save_libflags' not in env:
        env["_boost_save_libflags"] = env["_LIBFLAGS"]
        env['_LIBFLAGS'] = '${_boost_libflags(__env__)}'
        env['_boost_libflags'] = boost_libflags

    # Finally add the method for appending specific boost libraries
    env.AddMethod(_append_boost_library, "AppendBoostLibrary")
    env.AddMethod(boost_version, "BoostVersion")


def exists(env):
    return True
