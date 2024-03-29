# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
"""
Tool providing access to the CanFestival-3 CANopen API. Currently, we only
check /usr/local and system default (i.e., /usr) as possible install locations
for CanFestival libraries and headers.

The tool also provides a builder to generate CanFestival object dictionary
implementation files <foo>.c and <foo>.h from <foo>.od, e.g.,

    env.canfestivalObjdictImpl('myobj.od')

will cause generation of myobj.c and myobj.h if they are out of date w.r.t.
myobj.od.
"""

import os, os.path
import string
import SCons
import subprocess

_canfestival_source_file = """
#include <canfestival.h>
int main(int argc, char **argv)
{
    TimerInit();
    return 0;
}
"""

def CheckCanFestival(context):
    context.Message('Checking for CanFestival linking...')
    result = context.TryLink(_canfestival_source_file, '.c')
    context.Result(result)
    return result

# Emitter for objdictgen. We need this because "objdictgen foo.od foo.c"
# creates a foo.h file in addition to creating foo.c
def _od_emitter(target, source, env):
    for s in source:
        src = str(s)
        # strip extension from src
        head = os.path.splitext(src)[0]
        # append <head>.h to the target list
        target.append(head + '.h')

    return target, source

_settings = {}

# Empty builder proxy for CanFestival installations that do not have a working
# objdictgen (i.e., those without Python 2)
def _warn_no_objdictgen_build(source):
    print("=========")
    print("WARNING: The CanFestival installation does not have a working")
    print("objdictgen to create .c and .h files from", source)
    print("=========")

def _calculate_settings(env, settings):
    # Just check under "/usr/local" (for now), since that's the default install
    # location for CanFestival.
    prefix = '/usr/local'
    # Look in the typical locations for the CanFestival headers, and see
    # that the location gets added to the CPP paths.
    incpaths = [ os.path.join(prefix, 'include'),
                 os.path.join(prefix, 'include', 'canfestival') ]
    print("Checking for CanFestival headers in: ", incpaths)
    header = env.FindFile("canfestival.h", incpaths)
    headerdir = None
    settings['CPPPATH'] = [ ]
    if header:
        headerdir = header.get_dir().get_abspath()
        settings['CPPPATH'] = [ headerdir ]
    print("CanFestival headerdir is ", headerdir)

    # Now try to find the libraries, using the header as a hint.
    if not headerdir or headerdir.startswith("/usr/include"):
        msg = "Could not find CanFestival CANopen API header canfestival.h. Check config.log."
        raise SCons.Errors.StopError(msg)
    
    # Save the library path
    settings['LIBPATH'] = os.path.join(prefix, 'lib')
    
    # Binary path
    binpath = os.path.join(prefix, 'bin')

    #
    # Create a Builder to use objdictgen to generate <x>.c and <x>.h from <x>.od
    #
    # On systems where objdictgen always exits with an error (i.e., those
    # without Python 2), we use an internal build function that just prints a
    # warning.
    #
    objdictgen_path = os.path.join(binpath, 'objdictgen')
    if subprocess.run([objdictgen_path, '-h']).returncode == 0:
        settings['ODBUILDER'] = SCons.Builder.Builder(
                action = objdictgen_path + " $SOURCES $TARGET",
                suffix = '.c',
                src_suffix = '.od',
                emitter = _od_emitter)

    # Now test linking
    libs = ['canfestival_unix', 'canfestival', 'pthread', 'dl', 'rt']
    settings['LIBS'] = libs

    if env.GetOption('clean') or env.GetOption('help'):
        return

    clone = env.Clone()
    clone.Replace(LIBS=libs)
    clone.AppendUnique(CPPPATH=settings['CPPPATH'])
    clone.AppendUnique(LIBPATH=settings['LIBPATH'])
    conf = clone.Configure(custom_tests = { "CheckCanFestival" : CheckCanFestival })
    if not conf.CheckCanFestival():
        msg = "Failed to link to CanFestival CANopen API. Check config.log."
        raise SCons.Errors.StopError(msg)
    settings['LIBS'] = libs
    conf.Finish()

def generate(env):
    if not _settings:
        _calculate_settings(env, _settings)
    env.AppendUnique(CPPPATH = _settings['CPPPATH'])
    env.Append(LIBS = _settings['LIBS'])
    env.AppendUnique(LIBPATH = _settings['LIBPATH'])

    # If the CanFestival installation supports it, add the X.od -> X.c and X.h builder.
    if 'ODBUILDER' in _settings:
        env.Append(BUILDERS = {'canfestivalObjdictImpl' : _settings['ODBUILDER']})
    else:
        env.canfestivalObjdictImpl = _warn_no_objdictgen_build

    # Add -DCANFESTIVAL_LIBDIR='"<libdir>"' so that code can use the macro when
    # building paths for dynamically loading CanFestival driver libraries.
    env.Append(CPPDEFINES=('CANFESTIVAL_LIBDIR=\'"' + _settings['LIBPATH'] + '"\''))


def exists(env):
    return True

