# -*- python -*-

"""
This tool adds Qt5 include paths and libraries to the build
environment.  Qt5 is similar to Qt4 in that it is divided into many
different modules, and the modules can be applied to the environment
individually using either the EnableQtModules() method or by listing the
module as a tool.  For example, these are equivalent:

    qtmods = ['QtSvg', 'QtCore', 'QtGui', 'QtNetwork', 'QtSql', 'QtOpenGL']
    env.EnableQtModules(qtmods)

    env.Require(Split("qtsvg qtcore qtgui qtnetwork qtsql qtopengl"))

If a Qt5 module is optional, such as disabling the build of a Qt GUI
application when the QtGui module is not present, then the
return value from the EnableQtModules() method must be used:

    qt5Modules = Split('QtGui QtCore QtNetwork')
    if not env.EnableQtModules(qt5Modules):
        Return()

The qt5 tool must be included first to force all the subsequent qt modules to be
applied as qt5 modules instead of qt4.  The biggest difference is the location
of the header files and the library names contain libQt5<Module>.
"""

import re
import os

import SCons.Defaults
import SCons.Node
import SCons.Tool
import SCons.Util
from SCons.Variables import PathVariable
from SCons.Script import Scanner

import eol_scons.parseconfig as pc
import eol_scons
from eol_scons import Debug

_options = None
USE_PKG_CONFIG = "Using pkg-config"
myKey = "HAS_TOOL_QT5"

class ToolQt5Warning(SCons.Warnings.Warning):
    pass
class GeneratedMocFileNotIncluded(ToolQt5Warning):
    pass
class Qt5ModuleIssue(ToolQt5Warning):
    pass
SCons.Warnings.enableWarningClass(ToolQt5Warning)

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
    if not moc in includes:
        SCons.Warnings.warn(
            GeneratedMocFileNotIncluded,
            "Generated moc file '%s' is not included by '%s'" %
            (str(moc), str(cpp)))

def _find_file(filename, paths, node_factory):
    retval = None
    for dir in paths:
        node = node_factory(filename, dir)
        if node.rexists():
            return node
    return None

class _Automoc(object):
    """
    Callable class, which works as an emitter for Programs, SharedLibraries and
    StaticLibraries.
    """

    def __init__(self, objBuilderName):
        self.objBuilderName = objBuilderName

    def __call__(self, target, source, env):
        """
        Smart autoscan function. Gets the list of objects for the Program
        or Lib. Adds objects and builders for the special qt5 files.
        """
        if int(env.subst('$QT_AUTOSCAN')) == 0:
            return target, source

        # some shortcuts used in the scanner
        FS = SCons.Node.FS.default_fs
        objBuilder = getattr(env, self.objBuilderName)

        # some regular expressions:
        # Q_OBJECT detection
        q_object_search = re.compile(r'[^A-Za-z0-9]Q_OBJECT[^A-Za-z0-9]') 
        # cxx and c comment 'eater'
        #comment = re.compile(r'(//.*)|(/\*(([^*])|(\*[^/]))*\*/)')
        # CW: something must be wrong with the regexp. See also bug #998222
        #     CURRENTLY THERE IS NO TEST CASE FOR THAT

        # The following is kind of hacky to get builders working properly (FIXME)
        objBuilderEnv = objBuilder.env
        objBuilder.env = env
        mocBuilderEnv = env.Moc5.env
        env.Moc5.env = env

        # make a deep copy for the result; MocH objects will be appended
        out_sources = source[:]

        Debug("%s: scanning [%s] to add targets to [%s]." %
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
            if (not isinstance(obj, SCons.Node.FS.Entry)):
                try:
                    if (len(obj) != 1):
                        raise SCons.Errors.StopError("expected one source")
                    obj = obj[0]
                except:
                    errmsg = "qt5/_Automoc_ got a bad source object: "
                    errmsg += str(obj)
                    raise SCons.Errors.StopError(errmsg)

            if not obj.has_builder():
                # binary obj file provided
                Debug("scons: qt5: '%s' seems to be a binary. Discarded." % 
                      str(obj), env)
                continue

            cpp = obj.sources[0]
            if not SCons.Util.splitext(str(cpp))[1] in cxx_suffixes:
                Debug("scons: qt5: '%s' is not a C++ file. Discarded." % 
                      str(cpp), env)
                # c or fortran source
                continue
            #cpp_contents = comment.sub('', cpp.get_text_contents())
            cpp_contents = cpp.get_text_contents()
            h=None
            for h_ext in header_extensions:
                # try to find the header file in the corresponding source
                # directory
                hname = SCons.Util.splitext(cpp.name)[0] + h_ext
                h = _find_file(hname,
                              (cpp.get_dir(),),
                              FS.File)
                if h:
                    Debug("scons: qt5: Scanning '%s' (header of '%s')" % 
                          (str(h), str(cpp)), env)
                    #h_contents = comment.sub('', h.get_text_contents())
                    h_contents = h.get_text_contents()
                    break
            if not h:
                Debug("scons: qt5: no header for '%s'." % (str(cpp)), env)
            if h and q_object_search.search(h_contents):
                # h file with the Q_OBJECT macro found -> add moc_cpp
                moc_cpp = env.Moc5(h)
                moc_o = objBuilder(moc_cpp)
                out_sources.append(moc_o)
                #moc_cpp.target_scanner = SCons.Defaults.CScan
                Debug("scons: qt5: found Q_OBJECT macro in '%s', "
                      "moc'ing to '%s'" % (str(h), str(moc_cpp)), env)
            if cpp and q_object_search.search(cpp_contents):
                # cpp file with Q_OBJECT macro found -> add moc
                # (to be included in cpp)
                moc = env.Moc5(cpp)
                env.Ignore(moc, moc)
                Debug("scons: qt5: found Q_OBJECT macro in '%s', "
                      "moc'ing to '%s'" % (str(cpp), str(moc)), env)
                #moc.source_scanner = SCons.Defaults.CScan
        # restore the original env attributes (FIXME)
        objBuilder.env = objBuilderEnv
        env.Moc5.env = mocBuilderEnv

        return (target, out_sources)

AutomocShared = _Automoc('SharedObject')
AutomocStatic = _Automoc('StaticObject')

def _locateQt5Command(env, command) :
    # Check the cache
    cache = env.CacheVariables()
    key = "qt5_" + command
    result = cache.lookup(env, key)
    if result:
        return result

    # Look for <command>-qt5, followed by just <command>
    commandQt5 = command + '-qt5'
    cmds = [commandQt5, command]
    Debug("qt5: checking for commands: %s" % (cmds))

    qt5BinDir = None
    #
    # If env['QT5DIR'] is defined, add the associated bin directory to our
    # search path for the commands
    #
    if 'QT5DIR' in env:
        # If we're using pkg-config, assume all Qt5 binaries live in 
        # <prefix_from_pkgconfig>/bin.  This is slightly dangerous,
        # but seems to match all installation schemes I've seen so far,
        # and the "prefix" variable appears to always be available (again,
        # so far...).
        if env['QT5DIR'] == USE_PKG_CONFIG:
            qt5Prefix = pc.RunConfig(env, 'pkg-config --variable=prefix Qt5Core')
            qt5BinDir = os.path.join(qt5Prefix, 'bin')
        # Otherwise, look for Qt5 binaries in <QT5DIR>/bin
        else:
            qt5BinDir = os.path.join(env['QT5DIR'], 'bin')

    # If we built a qt5BinDir, check (only) there first for the command. 
    # This will make sure we get e.g., <myQT5DIR>/bin/moc ahead of 
    # /usr/bin/moc-qt5 in the case where we have a standard installation 
    # but we're trying to use a custom one by setting QT5DIR.
    if qt5BinDir:
        # check for the binaries in *just* qt5BinDir
        result = None
        for cmd in cmds:
            result = result or env.WhereIs(cmd, [qt5BinDir])

    # Check the default path
    if not result:
        Debug("qt5: checking path for commands: %s" % (cmds))
        result = env.Detect(cmds)

    if not result:
        msg = "Qt5 command " + commandQt5 + " (" + command + ")"
        if qt5BinDir:
            msg += " not in " + qt5BinDir + ","
        msg += " not in $PATH"
        raise SCons.Errors.StopError(msg)

    cache.store(env, key, result)
    return result


tsbuilder = None
qmbuilder = None
qrcscanner = None
qrcbuilder = None
uic5builder = None
mocBld = None

def _scanResources(node, env, path, arg):
    contents = node.get_text_contents()
    includes = qrcinclude_re.findall(contents)
    return includes


def create_builders():
    global tsbuilder, qmbuilder, qrcscanner, qrcbuilder, uic5builder, mocBld

    # Translation builder
    tsbuilder = SCons.Builder.Builder(action =
                                      '$QT5_LUPDATE $SOURCES -ts $TARGETS',
                                      multi=1)
    qmbuilder = SCons.Builder.Builder(action =['$QT5_LRELEASE $SOURCE',    ],
                                      src_suffix = '.ts',
                                      suffix = '.qm',
                                      single_source = True)

    # Resource builder
    qrcscanner = Scanner(name = 'qrcfile',
        function = _scanResources,
        argument = None,
        skeys = ['.qrc'])
    qrcbuilder = SCons.Builder.Builder(
        action='$QT5_RCC $QT5_QRCFLAGS $SOURCE -o $TARGET',
        source_scanner = qrcscanner,
        src_suffix = '$QT5_QRCSUFFIX',
        suffix = '$QT5_QRCCXXSUFFIX',
        prefix = '$QT5_QRCCXXPREFIX',
        single_source = True)
    uic5builder = SCons.Builder.Builder(action='$QT5_UIC5CMD',
                                        src_suffix='$QT5_UISUFFIX',
                                        suffix='$QT5_UICDECLSUFFIX',
                                        prefix='$QT5_UICDECLPREFIX',
                                        single_source = True)
    mocBld = SCons.Builder.Builder(action={}, prefix={}, suffix={})
    for h in header_extensions:
        mocBld.add_action(h, '$QT5_MOCFROMHCMD')
        mocBld.prefix[h] = '$QT5_MOCHPREFIX'
        mocBld.suffix[h] = '$QT5_MOCHSUFFIX'
    for cxx in cxx_suffixes:
        mocBld.add_action(cxx, '$QT5_MOCFROMCXXCMD')
        mocBld.prefix[cxx] = '$QT5_MOCCXXPREFIX'
        mocBld.suffix[cxx] = '$QT5_MOCCXXSUFFIX'


create_builders()


_pkgConfigKnowsQt5 = None

def checkPkgConfig(env):
    #
    # See if pkg-config knows about Qt5 on this system
    #
    global _pkgConfigKnowsQt5
    if _pkgConfigKnowsQt5 == None:
        check = pc.CheckConfig(env, 'pkg-config --exists Qt5Core')
        _pkgConfigKnowsQt5 = check
    return _pkgConfigKnowsQt5


def generate(env):
    """Add Builders and construction variables for qt5 to an Environment."""

    # Only need to setup any particular environment once.
    if myKey in env:
        return

    if env.get('QT_VERSION', 5) != 5:
        msg = str("Cannot require qt5 tool after another version "
                  "(%d) already loaded." % (env.get('QT_VERSION')))
        raise SCons.Errors.StopError(msg)
        
    env['QT_VERSION'] = 5

    global _options
    if not _options:
        _options = env.GlobalVariables()
        _options.AddVariables(PathVariable('QT5DIR',
            'Parent directory of qt5 bin, include and lib sub-directories.\n'
            'The default location is determined from the path to qt5 tools\n'
            'and from pkg-config, so QT5DIR typically does not need to be\n'
            'specified.', None, PathVariable.PathAccept))
        _options.AddVariables(PathVariable('QT5INCDIR',
            'Override the qt5 include directory when QT5DIR is set to a path.\n'
            'The default location is QT5DIR/include, but sometimes the system\n'
            'uses a path like /usr/include/qt5, so this allows\n'
            'setting QT5DIR=/usr but QT5INCDIR=/usr/include/qt5.',
            None, PathVariable.PathAccept))
    _options.Update(env)

    # 
    # Try to find the Qt5 installation location, trying in order:
    #    o command line QT5DIR option
    #    o OS environment QT5DIR
    #    o installation defined via pkg-config (this is the preferred method)
    #    o parent of directory holding moc-qt5 in the execution path
    #    o parent of directory holding moc in the execution path
    # At the end of checking, either env['QT5DIR'] will point to the
    # top of the installation, it will be set to USE_PKG_CONFIG, or 
    # we will raise an exception.
    #
    if ('QT5DIR' in env):
        pass
    elif ('QT5DIR' in os.environ):
        env['QT5DIR'] = os.environ['QT5DIR']
    elif (env['PLATFORM'] == 'win32'):
        print("""
For Windows, QT5DIR must be set on the command line or in the environment.
E.g.:
  scons QT5DIR='/c/QtSDK/Desktop/Qt/4.7.4/mingw'
""")
    elif checkPkgConfig(env):
        env['QT5DIR'] = USE_PKG_CONFIG
    else:
        moc = env.WhereIs('moc-qt5') or env.WhereIs('moc')
        if moc:
            env['QT5DIR'] = os.path.dirname(os.path.dirname(moc))
        elif os.path.exists('/usr/lib64/qt5'):
            env['QT5DIR'] = '/usr/lib64/qt5';
        elif os.path.exists('/usr/lib/qt5'):
            env['QT5DIR'] = '/usr/lib/qt5';

    env.AddMethod(enable_modules, "EnableQtModules")

    if 'QT5DIR' not in env:
	# Dont stop, just print a warning. Later, a user call of
	# EnableQtModules() will return False if QT5DIR is not found.

        errmsg = "Qt5 not found, try setting QT5DIR."
        # raise SCons.Errors.StopError, errmsg
        print(errmsg)
        return

    # the basics
    env['QT5_MOC'] = _locateQt5Command(env, 'moc')
    env['QT5_UIC'] = _locateQt5Command(env, 'uic')
    env['QT5_RCC'] = _locateQt5Command(env, 'rcc')
    env['QT5_LUPDATE'] = _locateQt5Command(env, 'lupdate')
    env['QT5_LRELEASE'] = _locateQt5Command(env, 'lrelease')

    # Should the qt5 tool try to figure out which sources are to be moc'ed ?
    env['QT_AUTOSCAN'] = 1

    # Some QT specific flags. I don't expect someone wants to
    # manipulate those ...
    env['QT5_UICDECLFLAGS'] = ''
    env['QT5_MOCFROMHFLAGS'] = ''
    env['QT5_MOCFROMCXXFLAGS'] = '-i'
    env['QT5_QRCFLAGS'] = ''

    # suffixes/prefixes for the headers / sources to generate
    env['QT5_MOCHPREFIX'] = 'moc_'
    env['QT5_MOCHSUFFIX'] = '$CXXFILESUFFIX'
    env['QT5_MOCCXXPREFIX'] = 'moc_'
    env['QT5_MOCCXXSUFFIX'] = '.moc'
    env['QT5_UISUFFIX'] = '.ui'
    env['QT5_UICDECLPREFIX'] = 'ui_'
    env['QT5_UICDECLSUFFIX'] = '.h'
    env['QT5_QRCSUFFIX'] = '.qrc',
    env['QT5_QRCCXXSUFFIX'] = '$CXXFILESUFFIX'
    env['QT5_QRCCXXPREFIX'] = 'qrc_'

    env.Append( BUILDERS = { 'Ts': tsbuilder } )
    env.Append( BUILDERS = { 'Qm': qmbuilder } )

    env.Append(SCANNERS = qrcscanner)
    env.Append( BUILDERS = { 'Qrc': qrcbuilder } )

    # Interface builder
    env['QT5_UIC5CMD'] = [
        SCons.Util.CLVar('$QT5_UIC $QT5_UICDECLFLAGS -o ${TARGETS[0]} $SOURCE'),
        ]
    env.Append( BUILDERS = { 'Uic5': uic5builder } )
    env.Append( BUILDERS = { 'Uic': uic5builder } )

    # Metaobject builder
    env['QT5_MOCFROMHCMD'] = (
        '$QT5_MOC $QT5_MOCFROMHFLAGS -o ${TARGETS[0]} $SOURCE')
    env['QT5_MOCFROMCXXCMD'] = [
        SCons.Util.CLVar('$QT5_MOC $QT5_MOCFROMCXXFLAGS -o ${TARGETS[0]} $SOURCE'),
        SCons.Action.Action(_checkMocIncluded,None)]
    env.Append( BUILDERS = { 'Moc5': mocBld } )
    env.Append( BUILDERS = { 'Moc': mocBld } )

    # er... no idea what that was for
    static_obj, shared_obj = SCons.Tool.createObjBuilders(env)
    static_obj.src_builder.append('Uic5')
    shared_obj.src_builder.append('Uic5')
    
    # We use the emitters of Program / StaticLibrary / SharedLibrary
    # to scan for moc'able files
    # We can't refer to the builders directly, we have to fetch them
    # as Environment attributes because that sets them up to be called
    # correctly later by our emitter.
    #env.AppendUnique(PROGEMITTER =[AutomocStatic],
    #                 SHLIBEMITTER=[AutomocShared],
    #                 LIBEMITTER  =[AutomocStatic],
    #                 # Of course, we need to link against the qt5 libraries
    #                 CPPPATH=[os.path.join('$QT5DIR', 'include')],
    #                 LIBPATH=[os.path.join('$QT5DIR', 'lib')],
    env.AppendUnique(PROGEMITTER =[AutomocStatic],
                     SHLIBEMITTER=[AutomocShared],
                     LIBEMITTER  =[AutomocStatic])

    # Qt5 requires PIC.  This may have to be adjusted by platform and
    # compiler.
    env.AppendUnique(CCFLAGS=['-fPIC'])

    env[myKey] = True


def _checkQtCore(env):
    if 'QT5_CORE_CHECK' in env:
        return env['QT5_CORE_CHECK']
    conf = env.Clone(LIBS=[]).Configure()
    hasQt = conf.CheckLibWithHeader('QtCore', 'QtCore/Qt', 'c++')
    conf.Finish()
    if not hasQt:
        Debug('QtCore/Qt header file not found. '
              'Do "scons --config=force" to redo the check. '
              'See config.log for more information', env)
    env['QT5_CORE_CHECK'] = hasQt
    return hasQt


no_pkgconfig_warned = []
def enable_modules(env, modules, debug=False) :

    # Return False if a module cannot be enabled, otherwise True
    import sys

    env.LogDebug("Entering qt5 enable_modules(%s) with sys.platform=%s..." %
                 (",".join(modules), sys.platform))
    if sys.platform.startswith("linux"):

        if 'QT5DIR' not in env:
            return False

        if debug:
            modules = [module + "_debug" for module in modules]
        for module in modules:
            if (env['QT5DIR'] == USE_PKG_CONFIG):
                Debug("enabling module %s through pkg-config" % (module), env)
                # pkg-config *package* names for Qt5 modules use Qt5 as the
                # prefix, e.g. Qt5 module 'QtCore' maps to pkg-config
                # package name 'Qt5Core'
                modPackage = module
                if modPackage.startswith('Qt'):
                    modPackage = "Qt5" + modPackage[2:]

                # Starting directory for headers.  First try 
                # 'pkg-config --variable=headerdir Qt'. If that's empty 
                # (this happens on CentOS 5 systems...), try 
                # 'pkg-config --variable=prefix QtCore' and append '/include'.
                hdir = pc.RunConfig(env, 'pkg-config --variable=headerdir Qt5')
                if (hdir == ''):
                    prefix = pc.RunConfig(env, 
                                          'pkg-config --variable=prefix Qt5Core')
                    if (prefix == ''):
                        print('Unable to build Qt header dir for adding module ' +
                              module)
                        return False
                    hdir = os.path.join(prefix, 'include')

                if pc.CheckConfig(env, 'pkg-config --exists ' + modPackage):
                    # Retrieve LIBS and CFLAGS separately, so CFLAGS can be
                    # added just once (unique=1).  Otherwise projects like
                    # ASPEN which require qt modules many times over end up
                    # with dozens of superfluous CPP includes and defines.
                    cflags = pc.RunConfig(env,
                                          'pkg-config --cflags ' + modPackage)
                    env.MergeFlags(cflags, unique=1)
                    libflags = pc.RunConfig(env,
                                            'pkg-config --libs ' + modPackage)
                    env.MergeFlags(libflags, unique=0)
                else:
                    # warn if we haven't already
                    if not (module in no_pkgconfig_warned):
                        print("Warning: No pkgconfig package " + modPackage +
                              " for Qt5/" + module + ", doing what I can...")
                        no_pkgconfig_warned.append(module)
                    # By default, the libraries are named with prefix Qt5
                    # rather than Qt, just like the module package name we
                    # built above.
                    env.Append(LIBS = [modPackage])
            else:
                Debug("enabling module %s with QT5DIR=%s" %
                      (module, env['QT5DIR']), env)
                # Module library directory can apparently be either
                # <QT5DIR>/lib/<module> or just <QT5DIR>/lib.  Use the
                # longer one if the directory exists, otherwise the shorter
                # one...  Likewise use the lib64 prefix if it exists, since
                # system installations on 64-bit hosts may only be
                # accessible in /usr/lib64/qt5/lib64.  Otherwise resort to
                # the usual 'lib' subdir, which sometimes exists even on
                # x86_64 .
                libpath = os.path.join(env['QT5DIR'], 'lib64')
                if not os.path.exists(libpath):
                    libpath = os.path.join(env['QT5DIR'], 'lib')
                longpath = os.path.join(libpath, module)
                if os.path.isdir(longpath):
                    libpath = longpath
                env.AppendUnique(LIBPATH = [libpath])

                # If this does not look like a system path, add it to
                # RPATH.  This is helpful when different components have
                # been built against different versions of Qt, but the one
                # specified by this tool is the one that should take
                # precedence.
                if not libpath.startswith('/usr/lib'):
                    env.AppendUnique(RPATH = [libpath])

                # It is possible to override the Qt5 include path with the
                # QT5INCDIR variable.  This is necessary when specifically
                # choosing the Qt5 system install by setting QT5DIR, but
                # the headers are in a subdirectory like /usr/include/qt5,
                # as is the case on Fedora.
                hdir = env.get('QT5INCDIR')
                if not hdir:
                    hdir = os.path.join(env['QT5DIR'], 'include')
                env.AppendUnique(CPPPATH = [hdir])
                # I tried taking out the module-specific header directory
                # from the include path here, to enforce the use of
                # module-qualified header includes, but that breaks qwt
                # header files.
                hcomp = module.replace('Qt5', 'Qt')
                env.AppendUnique(CPPPATH = [os.path.join(hdir, hcomp)])
                env.Append(LIBS = [module])

                if module == "QtGui":
                    env.AppendUnique(CPPDEFINES = ["QT_GUI_LIB"])

            # Kluge(?) so that moc can find the QtDesigner/QtUiPlugin headers
            #
            # This seems to be related to issues with moc-qt5 and headers
            # installed under /usr/include/qt5 rather than /usr/include.
            if module == "QtDesigner" or module == "QtUiPlugin":
                env.AppendUnique(QT5_MOCFROMHFLAGS =
                                  ['-I' + os.path.join(hdir, module)])

            # For QtCore at least, check that compiler can find the
            # library.  Do not propagate any current LIBS, since the
            # configure check does not depend on those, only on the current
            # paths and the compiler.  Otherwise scons will try to build
            # the library targets as part of the configure check, and that
            # causes all kinds of unexpected build behavior...
            skipconfig = env.GetOption('help') or env.GetOption('clean')
            if module == "Qt5Core" and not skipconfig:
                if not _checkQtCore(env):
                    return False

        # Explicitly add the default top of the header tree to the end of
        # moc's search path. This supports correct loading of qualified header
        # names.
        env.AppendUnique(QT5_MOCFROMHFLAGS = ['-I' + hdir])
        return True

    if sys.platform == "win32" :
        if 'QT5DIR' not in env:
            return False

        if debug : debugSuffix = 'd'
        else : debugSuffix = ''
        env.Append(LIBS=[lib+'5'+debugSuffix for lib in modules])
        if 'QtOpenGL' in modules:
            env.Append(LIBS=['opengl32'])
        env.AppendUnique(CPPPATH=[ '$QT5DIR/include/' ])
        env.AppendUnique(CPPPATH=[ '$QT5DIR/include/'+module
            for module in modules])
        env.AppendUnique(LIBPATH=['$QT5DIR/lib'])
        
    if sys.platform == "darwin" :
        # Use the frameworks on OSX 
        # Homebrew installs the frameworks in /usr/local/opt.
        env.AppendUnique(FRAMEWORKPATH=['$QT5DIR/lib',])

        modulesMac = []
        for module in modules:
            # Qt5 modules do not have Qt5 as the prefix, so remove that here.
            if module.startswith('Qt5'):
                module = "Qt" + module[3:]
            modulesMac.append(module)

# FRAMEWORKS appears not to be used in Sierra.  Caused "ld: framework not found QtWidget".
        env.AppendUnique(FRAMEWORKS=modulesMac)

        # Add include paths for the modules. One would think that the frameworks
        # would do this, but apparently not.
        for module in modulesMac:
            env.AppendUnique(CPPPATH=['$QT5DIR/lib/' + module + '.framework/Headers',])
        
    return True


def exists(env):
    return True


