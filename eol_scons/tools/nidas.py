"""
Modify an environment to build against NIDAS, inside or outside the source
tree.

This tool provides environment methods and variables useful for building
NIDAS programs and for building against the NIDAS libraries.  The
pseudo-builder methods create a Program builder but also add the NIDAS
library dependencies, add the standard clean and install targets, and also
add the program target to a global application map, so other Environments
which must run programs (ie, tests) can retrieve the right program node for
the current architecture using its common name.  They differ only in which
libraries are added to the LIBS variable automatically:

 env.NidasProgram()       -- Link with the full set of NIDAS libraries.
 env.NidasUtilProgram()   -- Link against only the NIDAS util library.
 env.NidasPlainProgram()  -- Do not add any NIDAS libraries to LIBS.

This tool adds methods to the environment for returning typical sets of
library names, suitable for adding to a LIBS construction variable:

 env.NidasUtilLibs()      -- Utility library and any of its dependencies.
 env.NidasLibs()          -- Full NIDAS libraries and dependencies.

The NidasProgram() method accepts a named parameter 'libs' to specify the
libraries explicitly.  For example, the call below is equivalent to
env.NidasUtilProgram():

 env.NidasProgram('utime', libs=env.NidasUtilLibs())

Program nodes can be added explicitly to the NIDAS application registry
using the method env.NidasAddApp().

When a SConscript needs to retrieve a NIDAS program from the registry, call
env.NidasApp():

 env.NidasApp('data_dump')

Besides returning the program node, this method also adds the program's
directory to the PATH.  The NIDAS library directories are also added to
LD_LIBRARY_PATH in the OS environment, so the program can be run through a
Command() builder.  So far this only works inside the source tree, but it
would be easy to create the program node to point to an installed program
when using this tool outside the nidas source tree.

This tool also applies tools for the NIDAS dependencies: xercesc and
xmlrpc.

The generate() function behaves differently depending upon whether it is
being applied to an environment inside or outside the nidas source tree.
However, the same methods and variables should be provided by the tool in
both cases, so that the same SConscript can work either way.
"""

import sys
import os
import subprocess
import re
import eol_scons
import sharedlibrary
from SCons.Variables import EnumVariable
import SCons.Warnings
from SCons.Script.SConscript import global_exports

class NidasPathNotDirectory(SCons.Warnings.Warning):
    pass

_options = None
USE_PKG_CONFIG = 'pkg-config'

_warned_paths = {}


def _applyInsideSource(env):
    # If ARCH is present and the NIDAS library source directories are
    # present, then build up the library nodes from the built targets.
    if not env.has_key('ARCH'):
        return False
    arch = env['ARCH']  # empty string for native builds

    if not os.path.exists(env.Dir('#/nidas/dynld').get_abspath()):
        return False

    libsyms = ['LIBNIDAS_UTIL','LIBNIDAS','LIBNIDAS_DYNLD']
    libmap = dict(zip(libsyms, libsyms))
    libpath = []
    for k in libmap.keys():
        if global_exports.has_key(k+arch):
            lib = global_exports[k+arch]
            libmap[k] = lib
            env[k] = lib
            libpath.append(lib.Dir(''))

    # Inside the  source tree, the build dir  paths have to come  first, to take
    # precedence over any  other library paths (ie OTHER_PREFIX)  added by other
    # tools or for third-party libraries.
    env.Prepend(LIBPATH = libpath)
    env.Tool("xercesc")
    env.Tool('xmlrpc')

    # Set LD_LIBRARY_PATH to the locally built libraries, for builders like
    # tests which want to run the nidas apps.  Also include nc_server_rpc,
    # in case it is not on the system path but NIDAS was built against it.
    ldlibdirs = [ l.Dir('').abspath for l in env.File(libmap.values()) ]
    env['ENV']['LD_LIBRARY_PATH'] = ":".join(ldlibdirs + ['/opt/nc_server/lib'])
    return True


_nidas_apps = {}

def _NidasAddApp(env, node):
    arch = env['ARCH']
    name = env.subst("${TARGET.filebase}", target=node)
    _nidas_apps[(name,arch)] = node

def _NidasProgram(env, target=None, source=None, libs=None):
    "Wrapper to build a program against full nidas libs and add it to apps."
    arch = env['ARCH']
    if not source:
        source = target
        target = None
    if libs is None:
        libs = _NidasLibs(env)
    node = env.Program(target=target, source=source, 
                       LIBS=env['LIBS'] + libs)
    inode = env.Install('$PREFIX/bin', node)
    env.Clean('install', inode)
    env.NidasAddApp(node)
    return node

def _NidasUtilProgram(env, target=None, source=None):
    "Wrapper to build a program against nidas util libs and add it to apps."
    return _NidasProgram(env, target, source, _NidasUtilLibs(env))

def _NidasPlainProgram(env, target=None, source=None):
    "Wrapper to build a plain program but with the nidas install extras."
    return _NidasProgram(env, target, source, [])


# The original idea was to add the explicit library targets to the LIBS
# construction variable, but then scons doesn't make the dependency
# connection, even though the link succeeds.  So resort to using the
# library names instead, whose dependencies scons resolves correctly thanks
# to the LIBPATH set when the nidas tool is applied.
def _NidasLibs(env):
    # return ['$LIBNIDAS','$LIBNIDAS_DYNLD','$LIBNIDAS_UTIL']
    return ['nidas','nidas_dynld','nidas_util']

def _NidasUtilLibs(env):
    # return ['$LIBNIDAS_UTIL']
    return ['nidas_util']

def _NidasApp(env, name):
    # If inside the source tree, look for the given app in the source tree
    # and setup to run against it.  If not inside, then look in the
    # installed path.
    if env.get('NIDAS_INSIDE_SOURCE'):
        app = _nidas_apps[(name, env['ARCH'])]
        path = env.subst("${TARGET.dir}", target=app)
        env.PrependENVPath('PATH', path)
        eol_scons.Debug("NidasApp(%s) resolved to %s, prepend %s to PATH, %s" %
                        (name, str(app), path,
                         "LD_LIBRARY_PATH=%s" % (env['ENV']['LD_LIBRARY_PATH'])))
    else:
        _NidasRuntimeENV(env)
        app = env.File('${NIDAS_PATH}/bin/'+name)
    return app


def _NidasRuntimeENV(env):
    "Setup the environment to run installed NIDAS programs."
    env.PrependENVPath('PATH', env.subst('${NIDAS_PATH}/bin'))
    libp = _resolve_libpaths(env, [env.subst('${NIDAS_PATH}')])
    if libp:
        env.PrependENVPath('LD_LIBRARY_PATH', libp[0])
    env.PrependENVPath('LD_LIBRARY_PATH', '/opt/nc_server/lib')


def _NidasAppFindFile(env, name):
    # Look for a program with the given name in either the build dir for
    # the active arch in the source tree, or else in the installed path.
    vdir = '#/build/build'
    if env.has_key('ARCH') and env['ARCH'] not in ['host', 'x86', '']:
        arch = env['ARCH']  # empty string for native builds
        vdir = vdir + '_' + arch
    vdir = env.Dir(vdir)
    eol_scons.Debug("Looking up app %s under %s..." % (name, vdir))
    nodes = env.arg2nodes([vdir], env.fs.Dir)
    app = SCons.Node.FS.find_file(name, tuple(nodes), verbose=True)
    # app = env.FindFile(name, [vdir])
    if not app:
        # Default to install bin using the prefix, which already contains
        # the arch distinction.
        vdir = env.Dir(env['PREFIX'])
        eol_scons.Debug("Looking up app %s under %s..." % (name, vdir))
        app = env.FindFile(name, [vdir])
    eol_scons.Debug("Found app: %s" % (str(app)))
    return app

def _check_nc_server(env, lib):
    lddcmd = ["ldd", lib]
    lddprocess = subprocess.Popen(lddcmd, stdout=subprocess.PIPE)
    found = False
    lddout = lddprocess.communicate()[0]
    return bool(re.search('libnc_server_rpc', lddout))


def _resolve_libpaths(env, paths):
    libdir = sharedlibrary.GetArchLibDir(env)
    libpaths = []
    for p in paths:
        parch = os.path.join(p, libdir)
        plib = os.path.join(p, 'lib')
        if os.path.exists(parch):
            libpaths.append(parch)
        elif os.path.exists(plib):
            libpaths.append(plib)
    return libpaths


def generate(env):
    # It is not (yet) possible to build against NIDAS on anything
    # except Linux, so don't even give anyone the option.
    if sys.platform == 'win32' or sys.platform == 'darwin':
    	env.EnableNIDAS = (lambda: 0)
        return

    inside = _applyInsideSource(env)
    env['NIDAS_INSIDE_SOURCE'] = inside
    eol_scons.Debug("applying nidas tool to %s, PREFIX=%s, %s source tree" %
                    (env.Dir('.').abspath, env.get('PREFIX'),
                     ['outside','inside'][int(inside)]))
    env.EnableNIDAS = (lambda: 0)
    env.AddMethod(_NidasLibs, "NidasLibs")
    env.AddMethod(_NidasUtilLibs, "NidasUtilLibs")
    env.AddMethod(_NidasAddApp, "NidasAddApp")
    env.AddMethod(_NidasApp, "NidasApp")
    env.AddMethod(_NidasRuntimeENV, "NidasRuntimeENV")
    env.AddMethod(_NidasProgram, "NidasProgram")
    env.AddMethod(_NidasUtilProgram, "NidasUtilProgram")
    env.AddMethod(_NidasPlainProgram, "NidasPlainProgram")

    if inside:
        env.EnableNIDAS = (lambda: 1)
        return

    # Default ARCH to native when outside the source tree.
    env['ARCH'] = ''

    global _options
    if not _options:
        default_nidas_path = env.get('NIDAS_PATH', USE_PKG_CONFIG)
        _options = env.GlobalVariables()
        _options.Add('NIDAS_PATH',
"""Set the NIDAS prefix paths, and enable builds of components
which use NIDAS. Setting it to empty disables NIDAS components.
This can be a comma-separated list of paths, for example to build
against a NIDAS installation whose other dependencies are installed
under another prefix.  Relative paths will be converted to absolute
paths relative to the top directory.
Set NIDAS_PATH to '""" + USE_PKG_CONFIG + """', the default, to use the settings from the system pkg-config.""",
                     default_nidas_path)
    _options.Update(env)
    if env.GetOption('help'):
        return

    nidas_paths = []
    nidas_libs = ['nidas','nidas_dynld','nidas_util']
    env['LIBNIDAS'] = 'nidas'
    env['LIBNIDAS_DYNLD'] = 'nidas_dynld'
    env['LIBNIDAS_UTIL'] = 'nidas_util'
    env.AppendUnique(DEPLOY_SHARED_LIBS=nidas_libs)

    if env['NIDAS_PATH'] == USE_PKG_CONFIG:
        try:
            # env['ENV'] may have PKG_CONFIG_PATH
            env.EnableNIDAS = subprocess.Popen(['pkg-config', 'nidas'],
                                               env=env['ENV']).wait() == 0
        except:
            pass
        if env.EnableNIDAS():
            print("Using pkg-config for nidas build variables")
            # Don't try here to make things unique in CFLAGS; just do an append
            env.ParseConfig('pkg-config --cflags --libs nidas', unique = False)
            env['NIDAS_PATH'] = USE_PKG_CONFIG
        else:
            # NIDAS_PATH explicitly requested it, but pkg-config wasn't found.
            raise SCons.Errors.StopError, "Cannot find pkgconfig file: 'pkg-config --exists nidas' failed"

    elif env['NIDAS_PATH'] != '':
        paths=env['NIDAS_PATH'].split(",")
        for p in paths:
            np = env.Dir("#").Dir(env.subst(p)).get_abspath()
            if not os.path.isdir(np):
                if not _warned_paths.has_key(np):
                    print("NIDAS path is not a directory: " + np)
                _warned_paths[np] = 1
            else:
                nidas_paths.append(np)
        if len(nidas_paths) == 0:
            raise NidasPathNotDirectory(
                "No directories found in NIDAS_PATH: %s; " % \
                    env['NIDAS_PATH'] + "disable NIDAS with NIDAS_PATH=''")
        env.EnableNIDAS = (lambda: 1)
        env.Append(CPPPATH=[os.path.join(p,'include') 
                            for p in nidas_paths])

        libpaths = _resolve_libpaths(env, nidas_paths)
        env.Append(LIBPATH=libpaths)

        # Find the nidas library so we can test it for nc_server_rpc.
        for p in env['LIBPATH']:
            pnidas = os.path.join(str(p), 'libnidas.so')
            if os.path.exists(pnidas):
                if _check_nc_server(env, pnidas):
                    nidas_libs += ['nc_server_rpc']
                    env.Append(LIBPATH=[p+'/../../nc_server/lib',
                                        '/opt/nc_server/lib'])
                break

        # The nidas library contains nidas_util already, so only the nidas
        # and nidas_dynld libraries need to be linked.  Linking nidas_util
        # causes static constructors to run multiple times (and
        # subsequently multiple deletes).
        env.Append(LIBS=nidas_libs)
        env.AppendUnique(RPATH=libpaths)
        # Anything using nidas is almost guaranteed now to have to link
        # with xerces.  Including some of the nidas headers creates direct
        # dependencies on xercesc symbols, even though an application may
        # not actually make any xercesc calls.  Such shared library
        # dependencies now have to be linked explicitly.
        env.Tool("xercesc")
        env.Tool('xmlrpc')

    else:
        # NIDAS_PATH explicitly disabled by setting it to the empty string.
        # No NIDAS dependencies will be added to the environment, and
        # EnableNIDAS() stays false.
        env.EnableNIDAS = (lambda: 0)



def exists(env):
    return True
