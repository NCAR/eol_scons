# -*- python -*-
import re
import os

import SCons.Defaults
import SCons.Node
import SCons.Tool
import SCons.Util
from SCons.Variables import PathVariable
from SCons.Script import Scanner
from SCons.Script import Configure

from eol_scons.parseconfig import RunConfig
from eol_scons.parseconfig import CheckConfig

_options = None
USE_PKG_CONFIG = "Using pkg-config"
myKey = "HAS_TOOL_QT4"

class ToolQt4Warning(SCons.Warnings.Warning):
    pass
class GeneratedMocFileNotIncluded(ToolQt4Warning):
    pass
class Qt4ModuleIssue(ToolQt4Warning):
    pass
SCons.Warnings.enableWarningClass(ToolQt4Warning)

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
        or Lib. Adds objects and builders for the special qt4 files.
        """
        try:
            if int(env.subst('$QT_AUTOSCAN')) == 0:
                return target, source
        except ValueError:
            pass
        try:
            debug = int(env.subst('$QT_DEBUG'))
        except ValueError:
            debug = 0
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
        mocBuilderEnv = env.Moc4.env
        env.Moc4.env = env

        # make a deep copy for the result; MocH objects will be appended
        out_sources = source[:]

        if debug:
            print("%s: scanning [%s] to add targets to [%s]." %
                  (self.objBuilderName, 
                   ",".join([str(s) for s in source]),
                   ",".join([str(t) for t in target])))
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
                        raise Error
                    obj = obj[0]
                except:
                    errmsg = "qt4/_Automoc_ got a bad source object: "
                    errmsg += str(obj)
                    raise SCons.Errors.StopError, errmsg                    

            if not obj.has_builder():
                # binary obj file provided
                if debug:
                    print "scons: qt4: '%s' seems to be a binary. Discarded." % str(obj)
                continue

            cpp = obj.sources[0]
            if not SCons.Util.splitext(str(cpp))[1] in cxx_suffixes:
                if debug:
                    print "scons: qt4: '%s' is not a C++ file. Discarded." % str(cpp) 
                # c or fortran source
                continue
            #cpp_contents = comment.sub('', cpp.get_contents())
            cpp_contents = cpp.get_contents()
            h=None
            for h_ext in header_extensions:
                # try to find the header file in the corresponding source
                # directory
                hname = SCons.Util.splitext(cpp.name)[0] + h_ext
                h = _find_file(hname,
                              (cpp.get_dir(),),
                              FS.File)
                if h:
                    if debug:
                        print "scons: qt4: Scanning '%s' (header of '%s')" % (str(h), str(cpp))
                    #h_contents = comment.sub('', h.get_contents())
                    h_contents = h.get_contents()
                    break
            if not h and debug:
                print "scons: qt4: no header for '%s'." % (str(cpp))
            if h and q_object_search.search(h_contents):
                # h file with the Q_OBJECT macro found -> add moc_cpp
                moc_cpp = env.Moc4(h)
                moc_o = objBuilder(moc_cpp)
                out_sources.append(moc_o)
                #moc_cpp.target_scanner = SCons.Defaults.CScan
                if debug:
                    print "scons: qt4: found Q_OBJECT macro in '%s', moc'ing to '%s'" % (str(h), str(moc_cpp))
            if cpp and q_object_search.search(cpp_contents):
                # cpp file with Q_OBJECT macro found -> add moc
                # (to be included in cpp)
                moc = env.Moc4(cpp)
                env.Ignore(moc, moc)
                if debug:
                    print "scons: qt4: found Q_OBJECT macro in '%s', moc'ing to '%s'" % (str(cpp), str(moc))
                #moc.source_scanner = SCons.Defaults.CScan
        # restore the original env attributes (FIXME)
        objBuilder.env = objBuilderEnv
        env.Moc4.env = mocBuilderEnv

        return (target, out_sources)

AutomocShared = _Automoc('SharedObject')
AutomocStatic = _Automoc('StaticObject')

def _locateQt4Command(env, command) :
    # Check the cache
    cache = env.CacheVariables()
    key = "qt4_" + command
    result = cache.lookup(env, key)
    if result:
        return result

    # Look for <command>-qt4, followed by just <command>
    commandQt4 = command + '-qt4'
    cmds = [commandQt4, command]

    qt4BinDir = None
    #
    # If env['QT4DIR'] is defined, add the associated bin directory to our
    # search path for the commands
    #
    if (env.has_key('QT4DIR')):
        # If we're using pkg-config, assume all Qt4 binaries live in 
        # <prefix_from_pkgconfig>/bin.  This is slightly dangerous,
        # but seems to match all installation schemes I've seen so far,
        # and the "prefix" variable appears to always be available (again,
        # so far...).
        if (env['QT4DIR'] == USE_PKG_CONFIG):
            qt4Prefix = RunConfig(env, 'pkg-config --variable=prefix QtCore')
            qt4BinDir = os.path.join(qt4Prefix, 'bin')
        # Otherwise, look for Qt4 binaries in <QT4DIR>/bin
        else:
            qt4BinDir = os.path.join(env['QT4DIR'], 'bin')

    # If we built a qt4BinDir, check (only) there first for the command. 
    # This will make sure we get e.g., <myQT4DIR>/bin/moc ahead of 
    # /usr/bin/moc-qt4 in the case where we have a standard installation 
    # but we're trying to use a custom one by setting QT4DIR.
    if (qt4BinDir):
        # check for the binaries in *just* qt4BinDir
        result = reduce(lambda a,b: a or env.WhereIs(b, [qt4BinDir]), 
                        cmds, None)

    # Check the default path
    if not result:
        result = env.Detect(cmds)

    if not result:
        msg = "Qt4 command " + commandQt4 + " (" + command + ")"
        if (qt4BinDir):
            msg += " not in " + qt4BinDir + ","
        msg += " not in $PATH"
        raise SCons.Errors.StopError, msg

    cache.store(env, key, result)
    return result


tsbuilder = None
qmbuilder = None
qrcscanner = None
qrcbuilder = None
uic4builder = None
mocBld = None

def _scanResources(node, env, path, arg):
    contents = node.get_contents()
    includes = qrcinclude_re.findall(contents)
    return includes


def create_builders():
    global tsbuilder, qmbuilder, qrcscanner, qrcbuilder, uic4builder, mocBld

    # Translation builder
    tsbuilder = SCons.Builder.Builder(action =
                                      '$QT4_LUPDATE $SOURCES -ts $TARGETS',
                                      multi=1)
    qmbuilder = SCons.Builder.Builder(action =['$QT4_LRELEASE $SOURCE',    ],
                                      src_suffix = '.ts',
                                      suffix = '.qm',
                                      single_source = True)

    # Resource builder
    qrcscanner = Scanner(name = 'qrcfile',
        function = _scanResources,
        argument = None,
        skeys = ['.qrc'])
    qrcbuilder = SCons.Builder.Builder(
        action='$QT4_RCC $QT4_QRCFLAGS $SOURCE -o $TARGET',
        source_scanner = qrcscanner,
        src_suffix = '$QT4_QRCSUFFIX',
        suffix = '$QT4_QRCCXXSUFFIX',
        prefix = '$QT4_QRCCXXPREFIX',
        single_source = True)
    uic4builder = SCons.Builder.Builder(action='$QT4_UIC4CMD',
                                        src_suffix='$QT4_UISUFFIX',
                                        suffix='$QT4_UICDECLSUFFIX',
                                        prefix='$QT4_UICDECLPREFIX',
                                        single_source = True)
    mocBld = SCons.Builder.Builder(action={}, prefix={}, suffix={})
    for h in header_extensions:
        mocBld.add_action(h, '$QT4_MOCFROMHCMD')
        mocBld.prefix[h] = '$QT4_MOCHPREFIX'
        mocBld.suffix[h] = '$QT4_MOCHSUFFIX'
    for cxx in cxx_suffixes:
        mocBld.add_action(cxx, '$QT4_MOCFROMCXXCMD')
        mocBld.prefix[cxx] = '$QT4_MOCCXXPREFIX'
        mocBld.suffix[cxx] = '$QT4_MOCCXXSUFFIX'


create_builders()


_pkgConfigKnowsQt4 = None

def checkPkgConfig(env):
    #
    # See if pkg-config knows about Qt4 on this system
    #
    global _pkgConfigKnowsQt4
    if _pkgConfigKnowsQt4 == None:
        check = (CheckConfig(env, 'pkg-config --exists QtCore') == 0)
        _pkgConfigKnowsQt4 = check
    return _pkgConfigKnowsQt4


def generate(env):
    """Add Builders and construction variables for qt4 to an Environment."""

    # Only need to setup any particular environment once.
    if env.has_key(myKey):
        return

    global _options
    if not _options:
        _options = env.GlobalVariables()
        _options.AddVariables(PathVariable('QT4DIR',
       'Parent directory of qt4 bin, include and lib sub-directories. The default location is determined from the path to qt4 tools and from pkg-config, so QT4DIR typically does not need to be specified.', None, PathVariable.PathAccept))
    _options.Update(env)

    # 
    # Try to find the Qt4 installation location, trying in order:
    #    o command line QT4DIR option
    #    o OS environment QT4DIR
    #    o installation defined via pkg-config (this is the preferred method)
    #    o parent of directory holding moc-qt4 in the execution path
    #    o parent of directory holding moc in the execution path
    # At the end of checking, either env['QT4DIR'] will point to the
    # top of the installation, it will be set to USE_PKG_CONFIG, or 
    # we will raise an exception.
    #
    if (env.has_key('QT4DIR')):
        pass
    elif (os.environ.has_key('QT4DIR')):
        env['QT4DIR'] = os.environ['QT4DIR']
    elif (env['PLATFORM'] == 'win32'):
        print
        print "For Windows, QT4DIR must be set" + \
            " on the command line or in the environment."
        print "E.g.:"
        print "    scons QT4DIR='/c/QtSDK/Desktop/Qt/4.7.4/mingw'"
        print
    elif checkPkgConfig(env):
        env['QT4DIR'] = USE_PKG_CONFIG
    else:
        moc = env.WhereIs('moc-qt4') or env.WhereIs('moc')
        if moc:
            env['QT4DIR'] = os.path.dirname(os.path.dirname(moc))
        elif os.path.exists('/usr/lib64/qt4'):
            env['QT4DIR'] = '/usr/lib64/qt4';
        elif os.path.exists('/usr/lib/qt4'):
            env['QT4DIR'] = '/usr/lib/qt4';

    import new
    env.EnableQt4Modules = new.instancemethod(enable_modules, env, type(env))

    if not env.has_key('QT4DIR'):
	# Dont stop, just print a warning. Later, a user call of
	# EnableQtModules() will return False if QT4DIR is not found.

        errmsg = "Qt4 not found, try setting QT4DIR."
        # raise SCons.Errors.StopError, errmsg
	print errmsg
	return

    # the basics
    env['QT4_MOC'] = _locateQt4Command(env, 'moc')
    env['QT4_UIC'] = _locateQt4Command(env, 'uic')
    env['QT4_RCC'] = _locateQt4Command(env, 'rcc')
    env['QT4_LUPDATE'] = _locateQt4Command(env, 'lupdate')
    env['QT4_LRELEASE'] = _locateQt4Command(env, 'lrelease')

    # Should the qt4 tool try to figure out which sources are to be moc'ed ?
    env['QT4_AUTOSCAN'] = 1

    # Some QT specific flags. I don't expect someone wants to
    # manipulate those ...
    env['QT4_UICDECLFLAGS'] = ''
    env['QT4_MOCFROMHFLAGS'] = ''
    env['QT4_MOCFROMCXXFLAGS'] = '-i'
    env['QT4_QRCFLAGS'] = ''

    # suffixes/prefixes for the headers / sources to generate
    env['QT4_MOCHPREFIX'] = 'moc_'
    env['QT4_MOCHSUFFIX'] = '$CXXFILESUFFIX'
    env['QT4_MOCCXXPREFIX'] = 'moc_'
    env['QT4_MOCCXXSUFFIX'] = '.moc'
    env['QT4_UISUFFIX'] = '.ui'
    env['QT4_UICDECLPREFIX'] = 'ui_'
    env['QT4_UICDECLSUFFIX'] = '.h'
    env['QT4_QRCSUFFIX'] = '.qrc',
    env['QT4_QRCCXXSUFFIX'] = '$CXXFILESUFFIX'
    env['QT4_QRCCXXPREFIX'] = 'qrc_'

    env.Append( BUILDERS = { 'Ts': tsbuilder } )
    env.Append( BUILDERS = { 'Qm': qmbuilder } )

    env.Append(SCANNERS = qrcscanner)
    env.Append( BUILDERS = { 'Qrc': qrcbuilder } )

    # Interface builder
    env['QT4_UIC4CMD'] = [
        SCons.Util.CLVar('$QT4_UIC $QT4_UICDECLFLAGS -o ${TARGETS[0]} $SOURCE'),
        ]
    env.Append( BUILDERS = { 'Uic4': uic4builder } )

    # Metaobject builder
    env['QT4_MOCFROMHCMD'] = (
        '$QT4_MOC $QT4_MOCFROMHFLAGS -o ${TARGETS[0]} $SOURCE')
    env['QT4_MOCFROMCXXCMD'] = [
        SCons.Util.CLVar('$QT4_MOC $QT4_MOCFROMCXXFLAGS -o ${TARGETS[0]} $SOURCE'),
        SCons.Action.Action(_checkMocIncluded,None)]
    env.Append( BUILDERS = { 'Moc4': mocBld } )

    # er... no idea what that was for
    static_obj, shared_obj = SCons.Tool.createObjBuilders(env)
    static_obj.src_builder.append('Uic4')
    shared_obj.src_builder.append('Uic4')
    
    # We use the emitters of Program / StaticLibrary / SharedLibrary
    # to scan for moc'able files
    # We can't refer to the builders directly, we have to fetch them
    # as Environment attributes because that sets them up to be called
    # correctly later by our emitter.
    #env.AppendUnique(PROGEMITTER =[AutomocStatic],
    #                 SHLIBEMITTER=[AutomocShared],
    #                 LIBEMITTER  =[AutomocStatic],
    #                 # Of course, we need to link against the qt4 libraries
    #                 CPPPATH=[os.path.join('$QT4DIR', 'include')],
    #                 LIBPATH=[os.path.join('$QT4DIR', 'lib')],
    env.AppendUnique(PROGEMITTER =[AutomocStatic],
                     SHLIBEMITTER=[AutomocShared],
                     LIBEMITTER  =[AutomocStatic])

    env[myKey] = True

no_pkgconfig_warned = []
def enable_modules(self, modules, debug=False) :

    # Return False if a module cannot be enabled, otherwise True
    import sys

    if sys.platform == "linux2" :

	if not self.has_key('QT4DIR'):
            return False

        if debug : modules = [module + "_debug" for module in modules]
        for module in modules:
            if (self['QT4DIR'] == USE_PKG_CONFIG):
                # Starting directory for headers.  First try 
                # 'pkg-config --variable=headerdir Qt'. If that's empty 
                # (this happens on CentOS 5 systems...), try 
                # 'pkg-config --variable=prefix QtCore' and append '/include'.
                hdir = RunConfig(self, 'pkg-config --variable=headerdir Qt')
                if (hdir == ''):
                    prefix = RunConfig(self, 
                                       'pkg-config --variable=prefix QtCore')
                    if (prefix == ''):
                        print('Unable to build Qt header dir for adding module ' +
                              module)
                        return False
                    hdir = os.path.join(prefix, 'include')

                if (CheckConfig(self, 'pkg-config --exists ' + module) == 0):
                    # Don't try here to make things unique in LIBS and
                    # CFLAGS; just do a simple append
                    flags = RunConfig(self, 
                                      'pkg-config --libs --cflags ' + module)
                    self.MergeFlags(flags, unique=0)
                else:
                    # warn if we haven't already
                    if not (module in no_pkgconfig_warned):
                        print("Warning: No pkgconfig for Qt4/" + module + 
                              ", doing what I can...")
                        no_pkgconfig_warned.append(module)
                    # Add -l<module>
                    self.Append(LIBS = [module])
                    # Add -I<Qt4HeaderDir>/<module>
                    self.AppendUnique(CPPPATH = [os.path.join(hdir, module)])
            else:
                # Module library directory can apparently be either
                # <QT4DIR>/lib/<module> or just <QT4DIR>/lib.  Use the
                # longer one if the directory exists, otherwise the shorter
                # one...  Likewise use the lib64 prefix if it exists, since
                # system installations on 64-bit hosts may only be
                # accessible in /usr/lib64/qt4/lib64.  Otherwise resort to
                # the usual 'lib' subdir, which sometimes exists even on
                # x86_64 .
                libpath = os.path.join(self['QT4DIR'], 'lib64')
                if not os.path.exists(libpath):
                    libpath = os.path.join(self['QT4DIR'], 'lib')
                longpath = os.path.join(libpath, module)
                if os.path.isdir(longpath):
                    libpath = longpath
                self.AppendUnique(LIBPATH = [libpath])
		# if this does not look like a system path, add it to
		# RPATH.  This is helpful when different components have
		# been built against differents versions of Qt, but the one
		# specified by this tool is the one that should take
		# precedence.
                if not libpath.startswith('/usr/lib'):
                    self.AppendUnique(RPATH = [libpath])

                hdir = os.path.join(self['QT4DIR'], 'include')
                self.AppendUnique(CPPPATH = [hdir])
                self.AppendUnique(CPPPATH = [os.path.join(hdir, module)])
                self.Append(LIBS = [module])

            # Kluge(?) so that moc can find the QtDesigner headers, necessary
            # at least for Fedora 6 and 7 (and CentOS 5)
            if module == "QtDesigner":
                self.AppendUnique(QT4_MOCFROMHFLAGS =
                                  ['-I', os.path.join(hdir, module)])
            if module == "QtGui":
                self.AppendUnique(CPPDEFINES = ["QT_GUI_LIB"])

            # For QtCore at least, check that compiler can find the library
            if module == "QtCore":
                conf = Configure(self,clean=False,help=False)
                hasQt = conf.CheckLibWithHeader('QtCore','QtCore/Qt','c++',autoadd=False)
                conf.Finish()
                if not hasQt:
                    # This print is a bit verbose, and not really a debug thing, so it's commented out.
                    # print "QtCore/Qt header file not found. Do \"scons --config=force\" to redo the check. See config.log for more information"
                    return hasQt
        return True

    if sys.platform == "win32" :
	if not self.has_key('QT4DIR'):
            return False

        if debug : debugSuffix = 'd'
        else : debugSuffix = ''
        self.Append(LIBS=[lib+'4'+debugSuffix for lib in modules])
        if 'QtOpenGL' in modules:
            self.Append(LIBS=['opengl32'])
        self.AppendUnique(CPPPATH=[ '$QT4DIR/include/' ])
        self.AppendUnique(CPPPATH=[ '$QT4DIR/include/'+module
            for module in modules])
        self.AppendUnique(LIBPATH=['$QT4DIR/lib'])
        
    if sys.platform == "darwin" :
        # Use the frameworks on OSX 
        # Homebrew installs the frameworks in /usr/local/lib.
        self.AppendUnique(FRAMEWORKPATH=['/usr/local/lib',])
        self.AppendUnique(FRAMEWORKS=modules)
        # Add include paths for the modules. One would think that the frameworks
        # would do this, but apparently not.
        for m in modules:
        	self.AppendUnique(CPPPATH=['/usr/local/lib/' + m + '.framework/Headers',])
        
    return True

def exists(env):
    return _detect(env)
