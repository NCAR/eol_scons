# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
import os
import os.path
import SCons
import eol_scons.parseconfig as pc

_netcdf_source_file = """
#include <netcdf.h>
int main(int argc, char **argv)
{
    const char* ncv = nc_inq_libvers();
    return 0;
}
"""


def CheckNetCDF(context):
    context.Message('Checking for netcdf linking...')
    result = context.TryLink(_netcdf_source_file, '.c')
    context.Result(result)
    return result


_settings = {}


def _calculate_settings(env, settings):

    prefix = env.subst(env.get('OPT_PREFIX', '/usr/local'))
    # Look in the typical locations for the netcdf headers, and see
    # that the location gets added to the CPP paths.
    incpaths = [os.path.join(prefix, 'include'),
                os.path.join(prefix, 'include', 'netcdf'),
                "/usr/include/netcdf-3",
                "/usr/include/netcdf"]
    # Netcdf 4.2 C++ API installs a /usr/include/netcdf header file,
    # which throws an exception in FindFile.  So cull the list of any
    # entries which are actually files.
    incpaths = [p for p in incpaths if os.path.isdir(p)]
    header = env.FindFile("netcdf.h", incpaths)
    headerdir = None
    settings['CPPPATH'] = []
    if header:
        headerdir = header.get_dir().get_abspath()
        settings['CPPPATH'] = [headerdir]

    # Now try to find the libraries, using the header as a hint.
    if not headerdir or headerdir.startswith("/usr/include"):
        # only check system install dirs since the header was not found
        # anywhere else.
        settings['LIBPATH'] = []
    else:
        # Assume libdir is same pattern as include directory.  See
        # code three lines down for corner cases that may crop up.
        libdir = headerdir.replace('include', 'lib')
        settings['LIBPATH'] = [libdir]

# Unused corner case.
#    if headerdir and headerdir.startswith("/usr/include/netcdf-3"):
#        settings['LIBPATH'] = ['/usr/lib/netcdf-3']

    # Now check whether the HDF libraries are needed explicitly when
    # linking with netcdf.  Use a cloned Environment so Configure does
    # not modify the original Environment.  Reset the LIBS so that
    # libraries in the original Environment do not break the linking,
    # ie, missing libraries or libraries with missing dependencies.
    # The CPPPATH and LIBPATH are preserved, since they will be in
    # effect when a program is built with this environment, and they
    # can change which netcdf library gets linked.

    libs = ['netcdf']
    settings['LIBS'] = libs

    if env.GetOption('clean') or env.GetOption('help'):
        return

    clone = env.Clone()
    clone.AppendUnique(CPPPATH=settings['CPPPATH'])
    clone.AppendUnique(LIBPATH=settings['LIBPATH'])
    conf = clone.Configure(custom_tests={"CheckNetCDF": CheckNetCDF})
    conf.env.Replace(LIBS=list(libs))
    if not conf.CheckNetCDF():
        # First attempt without HDF5 failed, so try with HDF5
        libs.append(['hdf5_hl', 'hdf5', 'bz2'])
        conf.env.Replace(LIBS=list(libs))
        if not conf.CheckNetCDF():
            msg = "Failed to link to netcdf both with and without"
            msg += " explicit HDF libraries.  Check config.log."
            raise SCons.Errors.StopError(msg)
    settings['LIBS'] = libs
    conf.Finish()

# Background on Configure check for netcdf linking: The first attempt
# directly used the Environment passed in.  That works as long as the
# Environment does not already contain dependencies (such as internal
# project libraries) which break the linking.  The other option was to
# create a brand new Environment.  However, if this tool is a global
# tool, then there will be infinite recursion trying to create the new
# Environment.  So the current approach clones the Environment, but
# then resets the LIBS list on the assumption that none of those
# dependencies are needed to link with netcdf.


def generate(env):
    # By now using pkg-config _should_ be all that is needed.  If it succeeds,
    # then the modifications made to the environment are presumed to be enough
    # to build against netcdf.  If it fails, then the searches in
    # _calculate_settings will still be tried.

    if pc.ParseConfig(env,
                      'pkg-config --silence-errors --cflags --libs netcdf'):
        return

    # The netcdf tool can avail itself of the settings in the prefixoptions
    # tool, but only if that tool has been required elsewhere first.  This
    # tool does not require it automatically in case that would introduce a
    # default /opt/local that interferes with building a project.

    if not _settings:
        _calculate_settings(env, _settings)
    env.AppendUnique(CPPPATH=_settings['CPPPATH'])
    env.Append(LIBS=_settings['LIBS'])
    env.AppendUnique(LIBPATH=_settings['LIBPATH'])


def exists(env):
    return True
