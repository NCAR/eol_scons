# -*- python -*-
#
# Tool providing access to the CanFestival-3 CANopen API. Currently, we only
# check /usr/local and system default (i.e., /usr) as possible install locations
# for CanFestival libraries and headers.
#

import os, os.path
import string
import SCons

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


_settings = {}

def _calculate_settings(env, settings):
    # Just check under "/usr/local" (for now), since that's the default install
    # location for CanFestival.
    prefix = '/usr/local'
    # Look in the typical locations for the CanFestival headers, and see
    # that the location gets added to the CPP paths.
    incpaths = [ os.path.join(prefix, 'include'),
                 os.path.join(prefix, 'include', 'canfestival') ]
    print "Checking for CanFestival headers in: ", incpaths
    header = env.FindFile("canfestival.h", incpaths)
    headerdir = None
    settings['CPPPATH'] = [ ]
    if header:
        headerdir = header.get_dir().get_abspath()
        settings['CPPPATH'] = [ headerdir ]
    print "CanFestival headerdir is ", headerdir

    # Now try to find the libraries, using the header as a hint.
    if not headerdir or headerdir.startswith("/usr/include"):
        # only check system install dirs since the header was not found
        # anywhere else.
        settings['LIBPATH'] = []
    else:
        # the header must have been found under OPT_PREFIX
        settings['LIBPATH'] = [os.path.join(prefix, 'lib')]

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
        raise SCons.Errors.StopError, msg
    settings['LIBS'] = libs
    conf.Finish()

def generate(env):
    if not _settings:
        _calculate_settings(env, _settings)
    env.AppendUnique(CPPPATH=_settings['CPPPATH'])
    env.Append(LIBS=_settings['LIBS'])
    env.AppendUnique(LIBPATH=_settings['LIBPATH'])
    # Add -DCANFESTIVAL_LIBDIR=<libdir> so that code can use the macro when
    # building paths for dynamically loading CanFestival driver libraries.
    if _settings['LIBPATH']: 
        env.Append(CPPDEFINES=('CANFESTIVAL_LIBDIR', '"' + _settings['LIBPATH'][0] + '"'))


def exists(env):
    return True

