# -*- python -*-

import os
import os.path
import platform
import string
import SCons

# APAR requires LROSE
dep_tools = ['lrose']

_apar_source_file = """
#include <AparData/AparTsInfo.hh>
int main(int argc, char **argv)
{
    AparTsInfo info;
    info.setDebug(AparTsDebug_t::OFF);
    return 0;
}
"""


def CheckApar(context):
    context.Message('Checking for APAR linking...')
    result = context.TryLink(_apar_source_file, '.cpp')
    context.Result(result)
    return result


_settings = {}

aparLibs = ['AparData']


def _calculate_settings(env, settings):
    # Look for LROSE under $LROSE_INSTALL_DIR, /usr/local/lrose,
    # or /opt/local/lrose
    prefix = None
    if ('APAR_INSTALL_DIR' in os.environ):
        paths = [os.environ['APAR_INSTALL_DIR']]
    else:
        paths = []
    paths += ['/usr/local/apar', '~/apar']
    for path in paths:
        if os.path.isdir(path):
            prefix = path
            break
    if not prefix:
        msg = "Unable to find APAR. No directory in [%s] exists." % (
            ', '.join(paths))
        raise SCons.Errors.StopError(msg)
    else:
        print("Using APAR directory", prefix)

    # Libs will be in <prefix>/lib64 or <prefix>/lib
    libdir = os.path.join(prefix, 'lib')
    if platform.machine()[-2:] == '64':
        libdir += '64'
    settings['LIBDIR'] = libdir

    # Headers will be in <prefix>/include
    headerdir = os.path.join(prefix, 'include')
    settings['CPPPATH'] = [headerdir]

    settings['LIBS'] = aparLibs

    if env.GetOption('clean') or env.GetOption('help'):
        return

    clone = env.Clone()
    clone.Replace(LIBS=aparLibs)
    clone.Require(dep_tools)
    clone.AppendUnique(CPPPATH=settings['CPPPATH'])
    clone.AppendUnique(LIBPATH=[settings['LIBDIR']])
    conf = clone.Configure(custom_tests={"CheckApar": CheckApar})
    found = conf.CheckApar()
    conf.Finish()
    if not found:
        msg = "Failed to link to APAR. Check config.log."
        raise SCons.Errors.StopError(msg)


def generate(env):
    if not _settings:
        _calculate_settings(env, _settings)
    env.Require(dep_tools)
    env.AppendUnique(CPPPATH=_settings['CPPPATH'])
    env.Append(LIBS=_settings['LIBS'])
    env.AppendUnique(LIBPATH=[_settings['LIBDIR']])
    env.AppendUnique(LINKFLAGS=['-Wl,-rpath,' + _settings['LIBDIR']])


def exists(env):
    return True
