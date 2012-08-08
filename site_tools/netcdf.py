# -*- python -*-

import os, os.path
import string
import SCons

netcdf_headers = string.split("""
ncvalues.h netcdf.h netcdf.hh netcdfcpp.h
""")

headers = [ os.path.join("$OPT_PREFIX","include",f)
            for f in netcdf_headers ]

# We extend the standard netcdf installation slightly by also copying
# the headers into a netcdf subdirectory, so headers can be qualified
# with a netcdf/ path when included.  Aeros does that, for example.

headers.extend ([ os.path.join("$OPT_PREFIX","include","netcdf",f)
                  for f in netcdf_headers ])
libs = string.split("""
$OPT_PREFIX/lib/libnetcdf.a
$OPT_PREFIX/lib/libnetcdf_c++.a
""")

# Try for eol_scons.package.Package, which will allow us to build netCDF
# from source if necessary.  If we don't find it, do stuff to disable 
# build-from-source.

netcdf_actions = None

try:
    from eol_scons.package import Package
    from eol_scons.chdir import MkdirIfMissing
    # Actions if we need to build netCDF from source
    netcdf_actions = [
        "./configure --prefix=$OPT_PREFIX FC= CC=gcc CXX=g++",
        "make",
        "make install",
        MkdirIfMissing("$OPT_PREFIX/include/netcdf") ] + [
        SCons.Script.Copy("$OPT_PREFIX/include/netcdf", h) for h in
        [ os.path.join("$OPT_PREFIX","include",h2) for h2 in netcdf_headers ]
        ]
except ImportError:
    # No build-from-source actions for netCDF if we didn't find the 
    # eol_scons stuff    

    # define a placeholder Package class
    class Package:
        def __init__(self, name, archive_targets, build_actions, 
                     install_targets, default_package_file = None):
            self.building = False
        
        def checkBuild(self, env):
            pass
    # empty command set since we won't build from source

# Note that netcdf.inc has been left out of this list, since this
# current setup does not install it.

class NetcdfPackage(Package):

    def __init__(self):
        dpf="ftp://ftp.unidata.ucar.edu/pub/netcdf/netcdf-3.6.2.tar.gz"
        Package.__init__(self, "NETCDF", "INSTALL",
                         netcdf_actions, libs + headers, dpf)
        self.settings = {}

    def require(self, env):
        "Need to add both c and c++ libraries to the environment."

        # The netcdf tool can avail itself of the settings in the
        # prefixoptions tool, but only if that tool has been required
        # elsewhere first.  This tool does not require it automatically in
        # case that would introduce a default /opt/local that interferes
        # with building a project.
        # env.Require('prefixoptions')
        if not self.settings:
            self.calculate_settings(env)
        self.apply_settings(env)

    def calculate_settings(self, env):
        Package.checkBuild(self, env)
        prefix = env.subst(env.get('OPT_PREFIX', '/usr/local'))
        # Look in the typical locations for the netcdf headers, and see
        # that the location gets added to the CPP paths.
        incpaths = [ os.path.join(prefix,'include'),
                     os.path.join(prefix,'include','netcdf'),
                     "/usr/include/netcdf-3",
                     "/usr/include/netcdf" ]
        # Netcdf 4.2 C++ API installs a /usr/include/netcdf header file,
        # which throws an exception in FindFile.  So cull the list of any
        # entries which are actually files.
        incpaths = [ p for p in incpaths if os.path.isdir(p) ]
        header = env.FindFile("netcdf.h", incpaths)
        headerdir = None
        self.settings['CPPPATH'] = [ ]
        if header:
            headerdir = header.get_dir().get_abspath()
            self.settings['CPPPATH'] = [ headerdir ]

        if self.building:
            self.settings['LIBS'] = [ env.File(libs[0]), env.File(libs[1]) ]
            # These refer to the nodes for the actual built libraries,
            # so there is no LIBPATH manipulation needed.
            return

        # Now try to find the libraries, using the header as a hint.
        if not headerdir or headerdir.startswith("/usr/include"):
            # only check system install dirs since the header was not found
            # anywhere else.
            self.settings['LIBPATH'] = []
        else:
            # the header must have been found under OPT_PREFIX
            self.settings['LIBPATH'] = [os.path.join(prefix,'lib')]

        if headerdir and headerdir.startswith("/usr/include/netcdf-3"):
            self.settings['LIBPATH'] = ['/usr/lib/netcdf-3']

        # Now check whether the HDF libraries are needed explicitly when
        # linking with netcdf.  Use a cloned Environment so Configure does
        # not modify the original Environment.  Also, reset the LIBS so
        # that libraries in the original Environment do not affect the
        # linking.  All the library link check needs is the netcdf-related
        # libraries.

        clone = env.Clone()
        libs = ['netcdf_c++', 'netcdf']
        clone.Replace(LIBS=libs)
        clone.Replace(CPPPATH=self.settings['CPPPATH'])
        clone.Replace(LIBPATH=self.settings['LIBPATH'])
        conf = clone.Configure()
        if not conf.CheckLib('netcdf'):
            # First attempt without HDF5 failed, so try with HDF5
            libs.append(['hdf5_hl', 'hdf5', 'bz2'])
            clone.Replace(LIBS=libs)
            if not conf.CheckLib('netcdf'):
                msg = "Failed to link to netcdf both with and without"
                msg += " explicit HDF libraries.  Check config.log."
                raise SCons.Errors.StopError, msg
        self.settings['LIBS'] = libs
        conf.Finish()


    def apply_settings(self, env):
        env.AppendUnique(CPPPATH=self.settings['CPPPATH'])
        env.Append(LIBS=self.settings['LIBS'])
        env.AppendUnique(LIBPATH=self.settings['LIBPATH'])



# Background on Configure check for netcdf linking: The first attempt
# directly used the Environment passed in.  That works as long as the
# Environment does not already contain dependencies (such as internal
# project libraries) which break the linking.  The other option was to
# create a brand new Environment.  However, if this tool is a global
# tool, then there will be infinite recursion trying to create the new
# Environment.  So the current approach clones the Environment, but
# then resets the LIBS list on the assumption that none of those
# dependencies are needed to link with netcdf.

netcdf_package = NetcdfPackage()

def generate(env):
    netcdf_package.require(env)

def exists(env):
    return True

