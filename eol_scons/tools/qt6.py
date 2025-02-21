# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
"""
This tool adds Qt6 include paths and libraries to the build
environment.  Qt6 is similar to Qt4 in that it is divided into many
different modules, and the modules can be applied to the environment
individually using either the EnableQtModules() method or by listing the
module as a tool.  For example, these are equivalent:

    qtmods = ['QtSvg', 'QtCore', 'QtGui', 'QtNetwork', 'QtSql', 'QtOpenGL']
    env.EnableQtModules(qtmods)

    env.Require(Split("qtsvg qtcore qtgui qtnetwork qtsql qtopengl"))

Note the case difference between tools and modules.  Qt tools follow the
convention of being all lower case.

If a Qt6 module is optional, such as disabling the build of a Qt GUI
application when the QtGui module is not present, then the return value
from the EnableQtModules() method can be used to see if the module is
present:

    qt6Modules = Split('QtGui QtCore QtNetwork')
    if not env.EnableQtModules(qt6Modules):
        Return()

The module detection uses the QT6DIR option setting.  Either it has been
set explicitly to a path or it is set to use pkg-config.  If Qt cannot be
located at that path, or it is not recognized by pkg-config, then all Qt
modules will return false.  The only way individual modules can be detected
is with pkg-config, since Qt6 settings may be found with pkg-config, but
then a particular module may not be installed and pkg-config for it will
fail.

The qt6 tool must be included first to force all the subsequent qt modules
to be applied as qt6 modules instead of qt4.  The biggest difference is the
location of the header files and the version-qualified library names like
libQt6<Module>.
"""

# Notes on install locations for each environment
#
# MSYS2
#
# pkg-conifg works
#
# There is no qmake...or it is in some other uninstalled package
# All other binaries are in /ucrt64/share/qt6/bin - in PATH

# MacOS - w/ Homebrew on x86_64
#
# pkg-config works.
#   Qt .pc files exist in non-standard location that is not searched.
#   /usr/local/opt/qt6/libexec/lib/pkgconfig
#
# qmake avaiable in standard qt path /usr/local/opt/qt6/bin - in PATH
# All other binaries (moc & uic) are in /usr/local/opt/qt/share/qt6/libexec/

# MacOS - w/ Homebrew on ARM
#
# pkg-config works.
#   /opt/homebrew/opt/qt/libexec/lib/pkgconfig
#
# qmake, lupdate, lrelease available in /opt/homebrew/opt/qt/bin - in PATH
# All other binaries (moc & uic) are in /opt/homebrew/opt/qt/share/qt/libexec
#

# Alma 9
#
# pkg-conifg works
#
# qmake avaiable in standard path /bin - in PATH
# All other binaries (moc & uic) are in /usr/lib64/qt6/libexec

import re
import os
import subprocess
import textwrap

import SCons.Defaults
import SCons.Node
import SCons.Tool
import SCons.Util
from SCons.Variables import PathVariable
from SCons.Script import Scanner

import eol_scons.parseconfig as pc
import eol_scons.debug as esd
from eol_scons import Debug

_options = None
USE_PKG_CONFIG = "Using pkg-config"
myKey = "HAS_TOOL_QT6"

# Known paths for executables -- other than qmake
libexecPaths = ['/usr/local/opt/qt/share/qt/libexec',
		'/opt/homebrew/opt/qt/share/qt/libexec',
		'/usr/lib64/qt6/libexec']

class ToolQt6Warning(SCons.Warnings.WarningOnByDefault):
    pass


class GeneratedMocFileNotIncluded(ToolQt6Warning):
    pass


class Qt6ModuleIssue(ToolQt6Warning):
    pass


qrcinclude_re = re.compile(r'<file[^>]*>([^<]*)</file>', re.M)


header_extensions = [".h", ".hxx", ".hpp", ".hh"]
if SCons.Util.case_sensitive_suffixes('.h', '.H'):
    header_extensions.append('.H')
cxx_suffixes = [".c", ".cxx", ".cpp", ".cc"]


def _checkMocIncluded(target, source, env):
    moc = target[0]
    cpp = source[0]
    # looks like cpp.includes is cleared before the build stage :-(
    # not really sure about the path transformations (moc.cwd? cpp.cwd?) :-/
    path = SCons.Defaults.CScan.path_function(env, moc.cwd)
    includes = SCons.Defaults.CScan(cpp, env, path)
    if moc not in includes:
        SCons.Warnings.warn(
            GeneratedMocFileNotIncluded,
            "Generated moc file '%s' is not included by '%s'" %
            (str(moc), str(cpp)))


def _find_file(filename, paths, node_factory):
    for d in paths:
        node = node_factory(filename, d)
        if node.rexists():
            return node
    return None


# This regular expression search can be rather slow, between reading in the
# whole file contents and then searching it.  It takes up more than 25% of the
# ASPEN scons startup.  The number of files scanned is not excessive, in that
# most of the files scanned will have Q_OBJECT.  Maybe the results could be
# cached between runs, but then how to know that the cache needs to be
# updated?  I suppose the scan results could be Value() nodes cached in
# sconsign, so they are not rescanned if the source files have not changed.
# Maybe other qt tool implementations have a better way.

# some regular expressions:
# Q_OBJECT detection
q_object_search = re.compile(r'\bQ_OBJECT\b')
# cxx and c comment 'eater'
# comment = re.compile(r'(//.*)|(/\*(([^*])|(\*[^/]))*\*/)')
# CW: something must be wrong with the regexp. See also bug #998222
#     CURRENTLY THERE IS NO TEST CASE FOR THAT


class _Automoc:
    """
    Callable class, which works as an emitter for Programs, SharedLibraries and
    StaticLibraries.
    """

    def __init__(self, objBuilderName):
        self.objBuilderName = objBuilderName

    def __call__(self, target, source, env):
        """
        Smart autoscan function. Gets the list of objects for the Program
        or Lib. Adds objects and builders for the special qt6 files.
        """
        if int(env.subst('$QT_AUTOSCAN')) == 0:
            return target, source

        # some shortcuts used in the scanner
        FS = SCons.Node.FS.default_fs
        objBuilder = getattr(env, self.objBuilderName)

        # The following is kind of hacky to get builders working properly
        # (FIXME)
        objBuilderEnv = objBuilder.env
        objBuilder.env = env
        mocBuilderEnv = env.Moc6.env
        env.Moc6.env = env

        # make a deep copy for the result; MocH objects will be appended
        out_sources = source[:]

        Debug("%s: scanning [%s] for Q_OBJECT sources to add targets "
              "to [%s]." %
              (self.objBuilderName,
               ",".join([str(s) for s in source]),
               ",".join([str(t) for t in target])), env)
        for obj in source:
            #
            # KLUGE: If the obj is not a SCons.Node.FS.Entry, it may be a list
            # containing only the entry.  If we get a list of length one, just
            # use its single entry as the obj.  Not sure why this has become
            # an issue now...
            #
            if isinstance(obj, list):
                if len(obj) != 1:
                    raise SCons.Errors.StopError("expected one source")
                obj = obj[0]
            if not isinstance(obj, SCons.Node.FS.Entry):
                errmsg = "qt6/_Automoc_ got a bad source object: "
                errmsg += str(obj)
                raise SCons.Errors.StopError(errmsg)

            if not obj.has_builder():
                # binary obj file provided
                Debug("scons: qt6: '%s' seems to be a binary. Discarded." %
                      str(obj), env)
                continue

            cpp = obj.sources[0]
            if not SCons.Util.splitext(str(cpp))[1] in cxx_suffixes:
                Debug("scons: qt6: '%s' is not a C++ file. Discarded." %
                      str(cpp), env)
                # c or fortran source
                continue
            # cpp_contents = comment.sub('', cpp.get_text_contents())
            cpp_contents = cpp.get_text_contents()
            h = None
            for h_ext in header_extensions:
                # try to find the header file in the corresponding source
                # directory
                hname = SCons.Util.splitext(cpp.name)[0] + h_ext
                h = _find_file(hname, (cpp.get_dir(),), FS.File)
                if h:
                    # h_contents = comment.sub('', h.get_text_contents())
                    h_contents = h.get_text_contents()
                    break
            if not h:
                Debug("scons: qt6: no header for '%s'." % (str(cpp)), env)
            if h and q_object_search.search(h_contents):
                Debug("scons: qt6: scanned '%s' (header of '%s') "
                      "for Q_OBJECT" %
                      (str(h), str(cpp)), env)
                # h file with the Q_OBJECT macro found -> add moc_cpp
                moc_cpp = env.Moc6(h)
                moc_o = objBuilder(moc_cpp)
                out_sources.append(moc_o)
                # moc_cpp.target_scanner = SCons.Defaults.CScan
                Debug("scons: qt6: found Q_OBJECT macro in '%s', "
                      "moc'ing to '%s'" % (str(h), str(moc_cpp)), env)
            if cpp and q_object_search.search(cpp_contents):
                Debug("scons: qt6: scanned '%s' for Q_OBJECT" %
                      (str(cpp)), env)
                # cpp file with Q_OBJECT macro found -> add moc
                # (to be included in cpp)
                moc = env.Moc6(cpp)
                env.Ignore(moc, moc)
                Debug("scons: qt6: found Q_OBJECT macro in '%s', "
                      "moc'ing to '%s'" % (str(cpp), str(moc)), env)
                # moc.source_scanner = SCons.Defaults.CScan
        # restore the original env attributes (FIXME)
        objBuilder.env = objBuilderEnv
        env.Moc6.env = mocBuilderEnv

        return (target, out_sources)


AutomocShared = _Automoc('SharedObject')
AutomocStatic = _Automoc('StaticObject')


def _locateQt6Command(env, command):
    # Check the cache
    cache = env.CacheVariables()
    key = "qt6_" + command
    result = cache.lookup(env, key)
    if result:
        return result

    # Look for <command>-qt6, followed by just <command>
    qtcommand = command + '-qt6'
    cmds = [qtcommand, command]
    Debug("qt6: checking for commands: %s" % (cmds))

    qtbindir = None
    #
    # If env['QT6DIR'] is defined, add the associated bin directory to our
    # search path for the commands
    #
    if 'QT6DIR' in env:
        # If we're using pkg-config, assume all Qt6 binaries live in
        # <prefix_from_pkgconfig>/bin.  This is slightly dangerous,
        # but seems to match all installation schemes I've seen so far,
        # and the "prefix" variable appears to always be available (again,
        # so far...).
        if env['QT6DIR'] == USE_PKG_CONFIG:
            qtprefix = pc.RunConfig(env, 'pkg-config --variable=prefix Qt6Core')
            qtbindir = os.path.join(qtprefix, 'bin')
        # Otherwise, look for Qt6 binaries in <QT6DIR>/bin
        else:
            qtbindir = os.path.join(env['QT6DIR'], 'bin')

    # If we built a qtbindir, check (only) there first for the command.
    # This will make sure we get e.g., <myQT6DIR>/bin/moc ahead of
    # /usr/bin/moc-qt6 in the case where we have a standard installation but
    # we're trying to use a custom one by setting QT6DIR.
    if qtbindir:
        # check for the binaries in *just* qtbindir
        result = None
        for cmd in cmds:
            result = result or env.WhereIs(cmd, [qtbindir])

    # Check the default path
    if not result:
        Debug("qt6: checking path for commands: %s" % (cmds))
        result = env.Detect(cmds)

    # Check know paths for Qt6 on all OS's
    if not result:
        for dir in libexecPaths:
            for cmd in cmds:
                result = result or env.WhereIs(cmd, [dir])


    if not result:
        msg = "Qt6 command " + qtcommand + " (" + command + ")"
        if qtbindir:
            msg += " not in " + qtbindir + ","
        msg += " not in $PATH"
        raise SCons.Errors.StopError(msg)

    cache.store(env, key, result)
    return result


tsbuilder = None
qmbuilder = None
qrcscanner = None
qrcbuilder = None
uic6builder = None
mocBld = None


def _scanResources(node, _env, _path, _arg):
    contents = node.get_text_contents()
    includes = qrcinclude_re.findall(contents)
    return includes


def create_builders():
    global tsbuilder, qmbuilder, qrcscanner, qrcbuilder, uic6builder, mocBld

    # Translation builder
    tsbuilder = SCons.Builder.Builder(
        action='$QT6_LUPDATE $SOURCES -ts $TARGETS', multi=1)
    qmbuilder = SCons.Builder.Builder(action=['$QT6_LRELEASE $SOURCE'],
                                      src_suffix='.ts', suffix='.qm',
                                      single_source=True)

    # Resource builder
    qrcscanner = Scanner(name='qrcfile', function=_scanResources,
                         argument=None, skeys=['.qrc'])
    qrcbuilder = SCons.Builder.Builder(
        action='$QT6_RCC $QT6_QRCFLAGS $SOURCE -o $TARGET',
        source_scanner=qrcscanner, src_suffix='$QT6_QRCSUFFIX',
        suffix='$QT6_QRCCXXSUFFIX', prefix='$QT6_QRCCXXPREFIX',
        single_source=True)
    uic6builder = SCons.Builder.Builder(action='$QT6_UIC6CMD',
                                        src_suffix='$QT6_UISUFFIX',
                                        suffix='$QT6_UICDECLSUFFIX',
                                        prefix='$QT6_UICDECLPREFIX',
                                        single_source=True)
    mocBld = SCons.Builder.Builder(action={}, prefix={}, suffix={})
    for h in header_extensions:
        mocBld.add_action(h, '$QT6_MOCFROMHCMD')
        mocBld.prefix[h] = '$QT6_MOCHPREFIX'
        mocBld.suffix[h] = '$QT6_MOCHSUFFIX'
    for cxx in cxx_suffixes:
        mocBld.add_action(cxx, '$QT6_MOCFROMCXXCMD')
        mocBld.prefix[cxx] = '$QT6_MOCCXXPREFIX'
        mocBld.suffix[cxx] = '$QT6_MOCCXXSUFFIX'


create_builders()


_pkgConfigKnowsQt6 = None


def checkPkgConfig(env):
    #
    # See if pkg-config knows about Qt6 on this system
    #
    global _pkgConfigKnowsQt6
    if _pkgConfigKnowsQt6 is None:
        check = pc.CheckConfig(env, 'pkg-config --exists Qt6Core')
        _pkgConfigKnowsQt6 = check
    return _pkgConfigKnowsQt6


def generate(env):
    """Add Builders and construction variables for qt6 to an Environment."""

    # Only need to setup any particular environment once.
    if myKey in env:
        return

    if env.get('QT_VERSION', 6) != 6:
        msg = str("Cannot require qt6 tool after another version "
                  "(%d) already loaded." % (env.get('QT_VERSION')))
        raise SCons.Errors.StopError(msg)

    env['QT_VERSION'] = 6

    global _options
    if not _options:
        _options = env.GlobalVariables()
        _options.AddVariables(PathVariable('QT6DIR', textwrap.dedent("""\
        Parent directory of qt6 bin, include and lib sub-directories.
        The default location is determined from the path to qt6 tools
        and from pkg-config, so QT6DIR typically does not need to be
        specified."""),
                                           env.get('QT6DIR', None),
                                           PathVariable.PathAccept))
        _options.AddVariables(PathVariable('QT6INCDIR', textwrap.dedent("""\
        Override the qt6 include directory when QT6DIR is set to a path.
        The default location is QT6DIR/include, but sometimes the system
        uses a path like /usr/include/qt6, so this allows
        setting QT6DIR=/usr but QT6INCDIR=/usr/include/qt6."""),
                                           env.get('QT6INCDIR', None),
                                           PathVariable.PathAccept))
    _options.Update(env)


    # MacOS specifics.  Qt6 pkg-config files are in a non-standard location.
    if env['PLATFORM'] == "darwin":
      env.PrependENVPath('PKG_CONFIG_PATH', env['BREW_PREFIX'] + '/opt/qt/libexec/lib/pkgconfig')
    # Windows specifics.  Qt6 pkg-config files are in a non-standard location.
    if env['PLATFORM'] in ['msys','win32']:
      env.PrependENVPath('PKG_CONFIG_PATH', '/ucrt64/lib/pkgconfig')


    # Try to find the Qt6 installation location, trying in order:
    #    o command line QT6DIR option
    #    o OS environment QT6DIR
    #    o installation defined via pkg-config (this is the preferred method)
    #    o parent of directory holding moc-qt6 in the execution path
    #    o parent of directory holding moc in the execution path
    # At the end of checking, either env['QT6DIR'] will point to the
    # top of the installation, it will be set to USE_PKG_CONFIG, or
    # we will raise an exception.
    #
    if ('QT6DIR' in env):
        pass
    elif ('QT6DIR' in os.environ):
        env['QT6DIR'] = os.environ['QT6DIR']
    elif checkPkgConfig(env):
        env['QT6DIR'] = USE_PKG_CONFIG
    else:
        moc = env.WhereIs('moc-qt6') or env.WhereIs('moc')
        if moc:
            env['QT6DIR'] = os.path.dirname(os.path.dirname(moc))
        elif os.path.exists('/usr/lib64/qt6'):
            env['QT6DIR'] = '/usr/lib64/qt6'
        elif os.path.exists('/usr/lib/qt6'):
            env['QT6DIR'] = '/usr/lib/qt6'

    env.AddMethod(enable_modules, "EnableQtModules")
    env.AddMethod(deploy_linux, "DeployQtLinux")

    if 'QT6DIR' not in env:
        # Dont stop, just print a warning. Later, a user call of
        # EnableQtModules() will return False if QT6DIR is not found.
        errmsg = "Qt6 not found, try setting QT6DIR."
        # raise SCons.Errors.StopError, errmsg
        print(errmsg)

    # the basics
    env['QT6_MOC'] = _locateQt6Command(env, 'moc')
    env['QT6_UIC'] = _locateQt6Command(env, 'uic')
    env['QT6_RCC'] = _locateQt6Command(env, 'rcc')
    env['QT6_LUPDATE'] = _locateQt6Command(env, 'lupdate')
    env['QT6_LRELEASE'] = _locateQt6Command(env, 'lrelease')

    # Should the qt6 tool try to figure out which sources are to be moc'ed ?
    env['QT_AUTOSCAN'] = 1

    # Some QT specific flags. I don't expect someone wants to
    # manipulate those ...
    env['QT6_UICDECLFLAGS'] = ''
    env['QT6_MOCFROMHFLAGS'] = ''
    env['QT6_MOCFROMCXXFLAGS'] = '-i'
    env['QT6_QRCFLAGS'] = ''

    # suffixes/prefixes for the headers / sources to generate
    env['QT6_MOCHPREFIX'] = 'moc_'
    env['QT6_MOCHSUFFIX'] = '$CXXFILESUFFIX'
    env['QT6_MOCCXXPREFIX'] = 'moc_'
    env['QT6_MOCCXXSUFFIX'] = '.moc'
    env['QT6_UISUFFIX'] = '.ui'
    env['QT6_UICDECLPREFIX'] = 'ui_'
    env['QT6_UICDECLSUFFIX'] = '.h'
    env['QT6_QRCSUFFIX'] = '.qrc',
    env['QT6_QRCCXXSUFFIX'] = '$CXXFILESUFFIX'
    env['QT6_QRCCXXPREFIX'] = 'qrc_'

    env.Append(BUILDERS={'Ts': tsbuilder})
    env.Append(BUILDERS={'Qm': qmbuilder})

    env.Append(SCANNERS=qrcscanner)
    env.Append(BUILDERS={'Qrc': qrcbuilder})

    # Interface builder
    env['QT6_UIC6CMD'] = [
        SCons.Util.CLVar(
            '$QT6_UIC $QT6_UICDECLFLAGS -o ${TARGETS[0]} $SOURCE'),
        ]
    env.Append(BUILDERS={'Uic6': uic6builder})
    env.Append(BUILDERS={'Uic': uic6builder})

    # Metaobject builder
    env['QT6_MOCFROMHCMD'] = (
        '$QT6_MOC $QT6_MOCFROMHFLAGS -o ${TARGETS[0]} $SOURCE')
    env['QT6_MOCFROMCXXCMD'] = [
        SCons.Util.CLVar('$QT6_MOC $QT6_MOCFROMCXXFLAGS '
                         '-o ${TARGETS[0]} $SOURCE'),
        SCons.Action.Action(_checkMocIncluded, None)]
    env.Append(BUILDERS={'Moc6': mocBld})
    env.Append(BUILDERS={'Moc': mocBld})

    # er... no idea what that was for
    static_obj, shared_obj = SCons.Tool.createObjBuilders(env)
    static_obj.src_builder.append('Uic6')
    shared_obj.src_builder.append('Uic6')

    # We use the emitters of Program / StaticLibrary / SharedLibrary
    # to scan for moc'able files
    # We can't refer to the builders directly, we have to fetch them
    # as Environment attributes because that sets them up to be called
    # correctly later by our emitter.
    # env.AppendUnique(PROGEMITTER =[AutomocStatic],
    #                 SHLIBEMITTER=[AutomocShared],
    #                 LIBEMITTER  =[AutomocStatic],
    #                 # Of course, we need to link against the qt6 libraries
    #                 CPPPATH=[os.path.join('$QT6DIR', 'include')],
    #                 LIBPATH=[os.path.join('$QT6DIR', 'lib')],
    env.AppendUnique(PROGEMITTER=[AutomocStatic],
                     SHLIBEMITTER=[AutomocShared],
                     LIBEMITTER=[AutomocStatic])

    # Qt6 requires PIC.  This may have to be adjusted by platform and
    # compiler.
    env.AppendUnique(CCFLAGS=['-fPIC'])

    env[myKey] = True


# Once one configure check determines if Qt is available, then very likely all
# of them will.
HasQt = None


def _checkQtCore(env):
    # The Configure() check here is not modifying the Environment passed in,
    # it is only confirming that compiling against Qt6Core succeeds.
    global HasQt
    if HasQt is not None:
        return HasQt
    env.LogDebug("running Configure check for QtCore...")
    # LIBS is reset here to avoid trying to link any libraries already
    # added to this environment, but that clears the Qt6Core library that
    # should have been added already (such as by pkg-config), so that's the
    # library explicitly provided to the check method.
    conf = env.Clone().Configure()
    conf.env['LIBS'] = list()
    hasqt = conf.CheckLibWithHeader('Qt6Core', 'QtCore/Qt', 'c++')
    conf.Finish()
    if not hasqt:
        Debug('QtCore/Qt header file not found. '
              'Do "scons --config=force" to redo the check. '
              'See config.log for more information', env)
    HasQt = hasqt
    return HasQt


no_pkgconfig_warned = []


def enable_modules(env, modules, debug=False):
    """
    Enable the given Qt modules in the given Environment for the current
    platform.  Return False if a module cannot be enabled, otherwise True.
    The platform-specific modifications are made in other functions.  This
    main entry point enforces a few things before calling the
    platform-specific code:

    The module name must be a Qt module name that is not qualified by the
    Qt version.  So QtCore is the module name in Qt4, Qt5 and Qt6.  This
    function specifically rejects module names starting with Qt4, Qt5 or Qt6.

    QT6DIR must be set in the Environment.  If not, then the Qt6 setup in
    generate() above did not succeed, and therefore no Qt6 modules can be
    enabled.
    """
    env.LogDebug("Entering qt6 enable_modules(%s) with platform=%s..." %
                 (",".join(modules), env['PLATFORM']))

    if 'QT6DIR' not in env:
        env.LogDebug("QT6DIR not set, cannot enable module.")
        return False

    onefailed = False
    for module in modules:
        if module.startswith('Qt6') or module.startswith('Qt5'):
            raise SCons.Errors.StopError(
                "Qt module names should not be qualified with "
                "the version: %s" % (module))
        ok = False
        if env['PLATFORM'] in ['posix', 'msys', 'win32']:
            ok = enable_module_linux(env, module, debug)
        if env['PLATFORM'] == "darwin":
            ok = enable_module_osx(env, module, debug)
# Unused at moment.
#        if env['PLATFORM'] in ['msys', 'win32']:
#            ok = enable_module_win(env, module, debug)
        onefailed = onefailed or not ok

    return onefailed


def qualify_module_name(module):
    """
    Convert the Qt module name to the version-qualified name.
    """
    if module.startswith('Qt') and not module.startswith('Qt6'):
        module = "Qt6" + module[2:]
    return module


def replace_drive_specs(pathlist):
    """
    Modify the given list in place.  For each node in pathlist, if the node
    path starts with a drive specifier like C:, replace it with a string
    path with the drive specifier replaced with an absolute path like /c.
    This preserves any list elements as nodes if their path does not need
    to be fixed.  Returns None.
    """
    for i, node in enumerate(pathlist):
        path = str(node)
        if path.startswith("C:"):
            pathlist[i] = path.replace('C:', '/c')
    return None


_qt6_header_path = None


def get_header_path(env):
    # Starting directory for headers.  First try
    # 'pkg-config --variable=headerdir Qt'. If that's empty
    # (this happens on CentOS 5 systems...), try
    # 'pkg-config --variable=prefix QtCore' and append '/include'.
    global _qt6_header_path
    hdir = _qt6_header_path
    if hdir:
        return hdir
    hdir = pc.RunConfig(
        env, 'pkg-config --silence-errors --variable=includedir Qt6Core')
    if hdir == '':
        prefix = pc.RunConfig(env, 'pkg-config --variable=prefix Qt6Core')
        if prefix == '':
            print('Unable to build Qt header dir for adding modules')
            return None
        hdir = os.path.join(prefix, 'include')
        _qt6_header_path = hdir
    return hdir


def enable_module_linux(env, module, debug=False):
    """
    On Linux, a Qt6 module is enabled either with the settings from
    pkg-config or else the settings are generated manually here.  The Qt
    module name does not contain the version, however the pkg-config
    packages *are* qualified with a version, so that is handled here.
    Likewise the library names include a version, so that is handled if a
    library must be added manually, without pkg-config.
    """
    if debug:
        module = module + "_debug"
    if env['QT6DIR'] == USE_PKG_CONFIG:
        Debug("enabling module %s through pkg-config" % (module), env)
        # pkg-config *package* names for Qt6 modules use Qt6 as the
        # prefix, e.g. Qt6 module 'QtCore' maps to pkg-config
        # package name 'Qt6Core'
        modpackage = qualify_module_name(module)
        hdir = get_header_path(env)

        # The pkg-config should at least return a library name, so if
        # RunConfig() returns nothing, treat that the same as if a
        # CheckConfig() had failed, to avoid running pkg-config twice.
        pkgc = 'pkg-config --cflags --libs ' + modpackage
        cflags = pc.RunConfig(env, pkgc)
        if cflags:
            env.LogDebug("Before qt6 mergeflags '%s': %s" %
                         (pkgc, esd.Watches(env)))
            env.MergeFlags(cflags, unique=1)
            env.LogDebug("After qt6 mergeflags '%s': %s" %
                         (cflags, esd.Watches(env)))
        else:
            # warn if we haven't already
            if not (module in no_pkgconfig_warned):
                print("Warning: No pkgconfig package " + modpackage +
                      " for Qt6/" + module + ", doing what I can...")
                no_pkgconfig_warned.append(module)
            # By default, the libraries are named with prefix Qt6
            # rather than Qt, just like the module package name we
            # built above.
            env.Append(LIBS=[modpackage])

        # On MSYS2 pkg-config is returning C: in the path, which scons then
        # adds a prefix (e.g. "plotlib/" in aeros).  Replace C: with /c,
        # but only on msys.
        if env['PLATFORM'] in ['msys', 'win32']:
            replace_drive_specs(env['CPPPATH'])
            replace_drive_specs(env.get('LIBPATH', []))

    else:
        Debug("enabling module %s with QT6DIR=%s" %
              (module, env['QT6DIR']), env)
        # Module library directory can apparently be either
        # <QT6DIR>/lib/<module> or just <QT6DIR>/lib.  Use the
        # longer one if the directory exists, otherwise the shorter
        # one...  Likewise use the lib64 prefix if it exists, since
        # system installations on 64-bit hosts may only be
        # accessible in /usr/lib64/qt6/lib64.  Otherwise resort to
        # the usual 'lib' subdir, which sometimes exists even on
        # x86_64 .
        libpath = os.path.join(env['QT6DIR'], 'lib64')
        if not os.path.exists(libpath):
            libpath = os.path.join(env['QT6DIR'], 'lib')
        longpath = os.path.join(libpath, module)
        if os.path.isdir(longpath):
            libpath = longpath
        env.AppendUnique(LIBPATH=[libpath])

        # It is possible to override the Qt6 include path with the
        # QT6INCDIR variable.  This is necessary when specifically
        # choosing the Qt6 system install by setting QT6DIR, but
        # the headers are in a subdirectory like /usr/include/qt6,
        # as is the case on Fedora.
        hdir = env.get('QT6INCDIR')
        if not hdir:
            hdir = os.path.join(env['QT6DIR'], 'include')
        env.AppendUnique(CPPPATH=[hdir])
        # I tried taking out the module-specific header directory
        # from the include path here, to enforce the use of
        # module-qualified header includes, but that breaks qwt
        # header files.
        env.AppendUnique(CPPPATH=[os.path.join(hdir, module)])
        # The module library names *are* qualified by the version.
        env.Append(LIBS=[qualify_module_name(module)])
        # Because for some reason this is what pkg-config does...
        mdef = "QT_" + module[2:].upper() + "_LIB"
        env.AppendUnique(CPPDEFINES=[mdef])

    # Kluge(?) so that moc can find the QtDesigner/QtUiPlugin headers
    #
    # This seems to be related to issues with moc-qt6 and headers
    # installed under /usr/include/qt6 rather than /usr/include.
    if module == "QtDesigner" or module == "QtUiPlugin":
        env.AppendUnique(
            QT6_MOCFROMHFLAGS=['-I' + os.path.join(hdir, module)])

    # For QtCore at least, check that compiler can find the
    # library.  Do not propagate any current LIBS, since the
    # configure check does not depend on those, only on the current
    # paths and the compiler.  Otherwise scons will try to build
    # the library targets as part of the configure check, and that
    # causes all kinds of unexpected build behavior...
    skipconfig = env.GetOption('help') or env.GetOption('clean')
    if module == "QtCore" and not skipconfig:
        # This may be here because it's useful to confirm that all the
        # configuration above actually works.  If we didn't need to return
        # a value indicating whether Qt is available, then this would be
        # unnecessary.
        if not _checkQtCore(env):
            return False

    # Explicitly add the default top of the header tree to the end of
    # moc's search path. This supports correct loading of qualified header
    # names.
    env.AppendUnique(QT6_MOCFROMHFLAGS=['-I' + hdir])
    return True


def enable_module_win(env, module, debug=False):
    if debug:
        debugsuffix = 'd'
    else:
        debugsuffix = ''
    env.Append(LIBS=[module+'6'+debugsuffix])
    if module == 'QtOpenGL':
        env.Append(LIBS=['opengl32'])
    env.AppendUnique(CPPPATH=['$QT6DIR/include/'])
    env.AppendUnique(CPPPATH=['$QT6DIR/include/'+module])
    env.AppendUnique(LIBPATH=['$QT6DIR/lib'])
    return True


def enable_module_osx(env, module, debug=False):
    """
    Use the frameworks on OSX.  Homebrew installs the frameworks in
    /usr/local/opt.  There is no support for enabling debug modules as on
    Windows and Linux.
    """

    env.AppendUnique(FRAMEWORKS=[module])
    if debug:
        print("Enabling debug for Qt6 modules has no effect on OSX.")

    # At this time we believe we can just use the enable_module_linux.
    return enable_module_linux(env, module, debug)


def deploy_linux(env):
    """
    Linux distributions need to include the xcb platform file and its
    dependencies, which don't get added when the deploy tool is used on the
    application because they don't show up as dependencies in ldd.

    - copy libqxcb into (application)/bin/platforms
    - copy Qt6DBus, Qt6XcbQpa, xcb-icccm, and xcb-render-util to
      (application)/lib
    """
    shared_libs = ['Qt6DBus', 'Qt6XcbQpa', 'xcb-icccm',
                   'xcb-render-util', 'xcb-image', 'xcb-keysyms']
    env.AppendUnique(DEPLOY_SHARED_LIBS=shared_libs)
    xcbpath = ""
    if env['QT6DIR'] == USE_PKG_CONFIG:
        pdir = pc.RunConfig(env, 'pkg-config --variable=plugindir Qt6')
        xcbpath = os.path.join(pdir, "platforms/libqxcb.so")
    else:
        xcbpath = os.path.join(env['QT6DIR'], "plugins/platforms/libqxcb.so")
    xcbnode = env.File(xcbpath)
    xcb = env.DeployProgram(xcbnode, DEPLOY_BINDIR="bin/platforms")
    return xcb


def exists(_env):
    return True
