# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
import os, os.path
import string
import SCons

# LROSE requires these tools which are not provided in the LROSE distribution
dep_tools=['z', 'fftw', 'bz2', 'boost_thread']

_lrose_source_file = """
#include <toolsa/udatetime.h>
int main(int argc, char **argv)
{
    date_time_t now;
    time_t then = uunix_time(&now);
    return 0;
}
"""

def CheckLROSE(context):
    context.Message('Checking for lrose linking...')
    result = context.TryLink(_lrose_source_file, '.c')
    context.Result(result)
    return result

_settings = {}

lroseLibs = ['dsdata', 'radar', 'Fmq', 'Spdb', 'Mdv', 'titan',
             'dsserver', 'Radx', 'Ncxx', 'rapformats',
             'euclid', 'rapmath', 'physics',
             'didss', 'toolsa', 'dataport', 'tdrp',
             'netcdf', 'pthread']

def _calculate_settings(env, settings):
    # Look for LROSE under $LROSE_INSTALL_DIR, /usr/local/lrose,
    # or /opt/local/lrose
    prefix = None
    if ('LROSE_INSTALL_DIR' in os.environ):
        paths = [os.environ['LROSE_INSTALL_DIR']]
    else:
        paths = []
    paths += ['/usr/local/lrose', '/opt/local/lrose']
    for path in paths:
        if os.path.isdir(path):
            prefix = path
            break
    if not prefix:
        msg = "Unable to find LROSE. No directory in [%s] exists." % (', '.join(paths))
        raise SCons.Errors.StopError(msg)
    else:
        print("Using LROSE directory", prefix)
    
    # Libs will be in <prefix>/lib
    libdir = os.path.join(prefix, 'lib')
    settings['LIBDIR'] = libdir
    
    # Headers will be in <prefix>/include
    headerdir = os.path.join(prefix, 'include')
    settings['CPPPATH'] = [ headerdir ]

    settings['LIBS'] = lroseLibs

    if env.GetOption('clean') or env.GetOption('help'):
        return

    clone = env.Clone()
    clone.Replace(LIBS=lroseLibs)
    clone.Require(dep_tools)
    clone.AppendUnique(CPPPATH=settings['CPPPATH'])
    clone.AppendUnique(LIBPATH=[settings['LIBDIR']])
    conf = clone.Configure(custom_tests = { "CheckLROSE" : CheckLROSE })
    if not conf.CheckLROSE():
        msg = "Failed to link to LROSE. Check config.log."
        raise SCons.Errors.StopError(msg)
    conf.Finish()

def generate(env):
    if not _settings:
        _calculate_settings(env, _settings)
    env.AppendUnique(CPPPATH=_settings['CPPPATH'])
    env.Append(LIBS=_settings['LIBS'])
    env.AppendUnique(LIBPATH=[_settings['LIBDIR']])
    env.AppendUnique(LINKFLAGS = ['-Wl,-rpath,' + _settings['LIBDIR']])
    env.Require(dep_tools)

def exists(env):
    return True

