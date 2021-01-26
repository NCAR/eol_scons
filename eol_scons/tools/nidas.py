"""
Modify an environment to build against NIDAS, inside or outside the source
tree.

If outside the source tree, then the NIDAS_PATH SCons Variable specifies
how to find the NIDAS installation.  By default the installation is found
with the system pkg-config, but if NIDAS_PATH is set to a path on the
system, then the NIDAS libraries, headers, and executables are found under
that path.  Either way this tool sets NIDAS_PREFIX to be the NIDAS prefix
path, whether discovered with pkg-config or set in NIDAS_PATH.  Do not use
NIDAS_PATH to derive paths with the NIDAS prefix, since it may have been
left with a default value or may not be a path at all.

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
Command() builder.

This tool also applies tools for the NIDAS dependencies: xercesc and
xmlrpc.

The generate() function behaves differently depending upon whether it is
being applied to an environment inside or outside the nidas source tree.
However, the same methods and variables should be provided by the tool in
both cases, so that the same SConscript can work either way.
"""
from __future__ import print_function

import sys
import os
import subprocess as sp
import re
import eol_scons
import eol_scons.parseconfig as pc
import sharedlibrary
import SCons.Warnings
from SCons.Script.SConscript import global_exports


class NidasPathNotDirectory(SCons.Warnings.WarningOnByDefault):
    pass


_options = None
USE_PKG_CONFIG = 'pkg-config'

_warned_paths = {}


def _setInsideSource(env):
    """
    If ARCH is present and the NIDAS library source directories are
    present, then this scons node is inside the NIDAS source tree.
    """
    inside = True
    if 'ARCH' not in env:
        inside = False
    if not os.path.exists(env.Dir('#/nidas/dynld').get_abspath()):
        inside = False
    env['NIDAS_INSIDE_SOURCE'] = inside
    return inside


def _applyInsideSource(env):
    """
    Build up the library nodes from the built targets.
    """
    arch = env['ARCH']  # empty string for native builds
    libsyms = ['LIBNIDAS_UTIL', 'LIBNIDAS', 'LIBNIDAS_DYNLD']
    libmap = dict(zip(libsyms, libsyms))
    libpath = []
    for k in libmap.keys():
        if k+arch in global_exports:
            lib = global_exports[k+arch]
            libmap[k] = lib
            env[k] = lib
            libpath.append(lib.Dir(''))

    # Inside the  source tree, the build dir  paths have to come  first, to
    # take precedence over any  other library paths (ie OTHER_PREFIX)  added
    # by other tools or for third-party libraries.
    env.Prepend(LIBPATH=libpath)
    env.Tool("xercesc")
    env.Tool('xmlrpc')

    # Set LD_LIBRARY_PATH to the locally built libraries, for builders like
    # tests which want to run the nidas apps.  Also include nc_server_rpc,
    # in case it is not on the system path but NIDAS was built against it.
    ldlibdirs = [env.File(l).Dir('').abspath for l in libmap.values()]
    env['ENV']['LD_LIBRARY_PATH'] = ":".join(ldlibdirs +
                                             ['/opt/nc_server/lib'])
    return True


_nidas_apps = {}


def _NidasAddApp(env, node):
    arch = env['ARCH']
    name = env.subst("${TARGET.filebase}", target=node)
    _nidas_apps[(name, arch)] = node


def _NidasProgram(env, target=None, source=None, libs=None):
    "Wrapper to build a program against full nidas libs and add it to apps."
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
    return ['nidas', 'nidas_dynld', 'nidas_util']


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
                         "LD_LIBRARY_PATH=%s" %
                         (env['ENV'].get('LD_LIBRARY_PATH'))))
    else:
        _NidasRuntimeENV(env)
        app = env.File('${NIDAS_PREFIX}/bin/'+name)
    return app


def _NidasRuntimeENV(env):
    "Setup the environment to run installed NIDAS programs."
    env.PrependENVPath('PATH', env.subst('${NIDAS_PREFIX}/bin'))
    libp = _resolve_libpaths(env, [env.subst('${NIDAS_PREFIX}')])
    if libp:
        env.PrependENVPath('LD_LIBRARY_PATH', libp[0])
    env.PrependENVPath('LD_LIBRARY_PATH', '/opt/nc_server/lib')


def _NidasAppFindFile(env, name):
    # Look for a program with the given name in either the build dir for
    # the active arch in the source tree, or else in the installed path.
    vdir = '#/build/build'
    if 'ARCH' in env and env['ARCH'] not in ['host', 'x86', '']:
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
    lddprocess = sp.Popen(lddcmd, stdout=sp.PIPE, env=env['ENV'])
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


def _addOptions(env, inside=False):
    global _options
    if not _options:
        default_nidas_path = env.get('NIDAS_PATH', USE_PKG_CONFIG)
        if inside:
            default_nidas_path = ''
        _options = env.GlobalVariables()
        _options.Add('NIDAS_PATH', """
Set the NIDAS prefix paths to build against, and enable builds of
components which use NIDAS. Setting this to empty outside the NIDAS source
tree disables components which need NIDAS.  Within the NIDAS source tree, this
variable is empty by default, which builds against the libraries and
header files built within the source tree.

This setting can be a comma-separated list of paths, for example to build
against a NIDAS installation whose other dependencies are installed under
another prefix.  Relative paths will be converted to absolute paths
relative to the top directory.  Set NIDAS_PATH to '%s' to use
the settings from the system pkg-config.""" % (USE_PKG_CONFIG),
                     default_nidas_path)
    _options.Update(env)


def generate(env):
    # It is not (yet) possible to build against NIDAS on anything
    # except Linux, so don't even give anyone the option.
    if sys.platform == 'win32' or sys.platform == 'darwin':
        env.EnableNIDAS = (lambda: 0)
        return

    env.EnableNIDAS = (lambda: 0)
    env.AddMethod(_NidasLibs, "NidasLibs")
    env.AddMethod(_NidasUtilLibs, "NidasUtilLibs")
    env.AddMethod(_NidasAddApp, "NidasAddApp")
    env.AddMethod(_NidasApp, "NidasApp")
    env.AddMethod(_NidasRuntimeENV, "NidasRuntimeENV")
    env.AddMethod(_NidasProgram, "NidasProgram")
    env.AddMethod(_NidasUtilProgram, "NidasUtilProgram")
    env.AddMethod(_NidasPlainProgram, "NidasPlainProgram")

    inside = _setInsideSource(env)

    # For now, do not add the NIDAS_PATH option when building inside the
    # nidas source tree, since that does not work with the existing nidas
    # SConscript files, but including the option in the help info could
    # cause confusion.
    if not inside:
        _addOptions(env)
    if env.GetOption('help'):
        return

    eol_scons.Debug("applying nidas tool to %s, PREFIX=%s, "
                    "%s source tree, NIDAS_PATH=%s" %
                    (env.Dir('.').abspath, env.get('PREFIX'),
                     ['outside', 'inside'][int(inside)],
                     env.get('NIDAS_PATH', '<na>')))

    # First check if inside the tree and nidas prefix not overridden.
    if inside and not env.get('NIDAS_PATH'):
        _applyInsideSource(env)
        env.EnableNIDAS = (lambda: 1)
        return

    # Default ARCH to native when outside the source tree, and make sure
    # NIDAS_INSIDE_SOURCE is overridden if actually building against an
    # installed nidas.
    env['ARCH'] = ''
    env['NIDAS_INSIDE_SOURCE'] = False

    nidas_paths = []
    nidas_libs = ['nidas', 'nidas_dynld', 'nidas_util']
    env['LIBNIDAS'] = 'nidas'
    env['LIBNIDAS_DYNLD'] = 'nidas_dynld'
    env['LIBNIDAS_UTIL'] = 'nidas_util'
    env.AppendUnique(DEPLOY_SHARED_LIBS=nidas_libs)

    if env['NIDAS_PATH'] == USE_PKG_CONFIG:
        try:
            # env['ENV'] may have PKG_CONFIG_PATH
            exists = pc.CheckConfig(env, 'pkg-config nidas')
            env.EnableNIDAS = (lambda: exists)
        except Exception:
            pass
        if env.EnableNIDAS():
            print("Using pkg-config for nidas build variables")
            # Don't try here to make things unique in CFLAGS; just do an append
            pc.ParseConfig(env, 'pkg-config --cflags --libs nidas',
                           unique=False)
            # Set NIDAS_PREFIX from the pkg-config prefix.
            env['NIDAS_PREFIX'] = pc.PkgConfigPrefix(
                env, 'nidas', default_prefix='/opt/nidas')
            env.LogDebug('NIDAS_PREFIX set from pkg-config: %s' %
                         (env['NIDAS_PREFIX']))
            env['NIDAS_LD_RUN_PATH'] = pc.RunConfig(
                env, "pkg-config --libs-only-L nidas").lstrip("-L")

        else:
            # NIDAS_PATH explicitly requested it, but pkg-config wasn't found.
            raise SCons.Errors.StopError("Cannot find pkgconfig file: "
                                         "'pkg-config --exists nidas' failed")

    elif env['NIDAS_PATH'] != '':
        paths = env['NIDAS_PATH'].split(",")
        for p in paths:
            np = env.Dir("#").Dir(env.subst(p)).get_abspath()
            if not os.path.isdir(np):
                if np not in _warned_paths:
                    print("NIDAS path is not a directory: " + np)
                _warned_paths[np] = 1
            else:
                nidas_paths.append(np)
        if len(nidas_paths) == 0:
            SCons.Warnings.warn(
                NidasPathNotDirectory,
                "No directories found in NIDAS_PATH: %s; " %
                env['NIDAS_PATH'] + "disable NIDAS with NIDAS_PATH=''")
        env.EnableNIDAS = (lambda: 1)
        env.Append(CPPPATH=[os.path.join(p, 'include')
                            for p in nidas_paths])

        libpaths = _resolve_libpaths(env, nidas_paths)
        env.Append(LIBPATH=libpaths)

        # Find the nidas library so we can test it for nc_server_rpc.
        elibpath = env['LIBPATH']
        nidas_prefix = None
        for p in elibpath:
            pnidas = os.path.join(str(p), 'libnidas.so')
            if os.path.exists(pnidas):
                nidas_prefix = os.path.dirname(str(p))
                env['NIDAS_LD_RUN_PATH'] = str(p)
                # Suspend this check for now.  If nidas was built against
                # nc_server, as is usually the case, then the link should
                # work even without specifying the nc_server library since
                # it's named in the nidas_dynld library.  This may need to
                # be revisited for the corner cases where nc_server is not
                # installed in a system location.
                if False and _check_nc_server(env, pnidas):
                    # Really the only support for building with nc_server
                    # is using pkg-config, so use it.  Pass any
                    # PKG_CONFIG_PATH settings into the process environment
                    # so it can be overridden, but beware, that changes the
                    # path for all other calls to pkg-config by this
                    # environment.
                    #
                    pc.PassPkgConfigPath(env)
                    env.ParseConfig('pkg-config --cflags --libs nc_server')
                break

        env['NIDAS_PREFIX'] = nidas_prefix
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
