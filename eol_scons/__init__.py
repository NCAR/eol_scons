# -*- python -*-
"""
The eol_scons package for EOL extensions to standard SCons.

This package extends SCons in three ways: it overrides or adds methods for
the SCons Environment class.  See the _ExtendEnvironment() function to see
the full list.

Second, this package adds a set of EOL tools to the SCons tool path.  Most
of the tools for configuring and building against third-party software
packages.

Lastly, this module itself provides an interface of a few functions, for
configuring and controlling the eol_scons framework outside of the
Environment methods.  These are the public functions:

GlobalVariables(): Returns the global set of variables (formerly known as
options) available in this source tree.

SetDebug(enable): set the global debugging flag to 'enable'.

Debug(msg): Print a debug message if the global debugging flag is true.

Nothing else in this module should be called from outside the package.  In
particular, all the symbols starting with an underscore are meant to be
private.  See the README file for the documenation for this module.
"""

import os
import re
import glob
import traceback

import SCons
import SCons.Tool


from SCons.Script import Variables
from SCons.Script import Environment
from SCons.Script import DefaultEnvironment
from SCons.Script import PackageVariable
from SCons.Script import EnumVariable
from SCons.Script import BoolVariable

from SCons.Util import NodeList
from SCons.Script.SConscript import global_exports
from SCons.Builder import _null

import string
import eol_scons.chdir

_eolsconsdir = os.path.dirname(__file__)

from SCons.Script import ARGUMENTS

debug = False

def SetDebug(enable):
    """Set the flag to enable or disable printing of debug messages."""
    global debug
    debug = enable

def Debug(msg):
    """Print a debug message if the global debugging flag is true."""
    global debug
    if debug:
        print msg

# I wish this would work, but apparently ARGUMENTS has not been populated
# yet when eol_scons is loaded.
#
# print("ARGUMENTS=%s" % (ARGUMENTS))
# SetDebug(ARGUMENTS.get('eolsconsdebug', 0))

Debug("Loading eol_scons @ %s" % (_eolsconsdir))

# ================================================================
# The public interface for the eol_scons package.
# ================================================================

global_variables = None

# We have to use a 'hardcoded' path to the config file rather than using
# the DefaultEnvironment() to create a path.  Otherwise creating the
# DefaultEnvironment causes this module to be called again setting up all
# kinds of weird and hard-to-diagnose behaviors.

default_cfile = "config.py"

def GlobalVariables(cfile = None):
    """Return the eol_scons global options."""
    global global_variables
    if not global_variables:
        global default_cfile
        if not cfile:
            cfile = default_cfile
        if not cfile.startswith("/"):
            # Turn relative config file path to absolute, relative
            # to top directory.
            cfile = os.path.abspath(os.path.join(__path__[0], 
                                                 "../..", cfile))
        default_cfile = cfile
        global_variables = Variables (cfile)
        global_variables.AddVariables(
            BoolVariable('eolsconsdebug',
                         'Enable debug messages from eol_scons.',
                         debug))
        print "Config files: %s" % (global_variables.files)
    return global_variables

# Alias for temporary backwards compatibility
GlobalOptions = GlobalVariables

_global_tools = {}


# ================================================================
# End of public interface
# ================================================================


def _fix_paths(list,env):
    """
    Remove duplicates from the path list, and keep local paths first.

    We need to call RDirs to convert paths like # to the correct form.
    However, RDirs gives us back nodes rather than strings, so the nodes
    are converted to string here so that _atd_concat does not treat them
    like special targets that do not need to be prefixed.
    """
    if env.has_key("RDirs"):
        list = env["RDirs"](list)
    ret = []
    for x in list:
        x = str(x)
        if x in ret:
            continue
        # print "Adding ", str(x)
        if x.startswith("/"):
            ret.append(x)
        else:
            ret.insert(0, x)
    # print "Leaving fix_paths()"
    return ret



def _fix_libs(list,env):
    "Leave only the last instance of each library in the list."
    ret = []
    for x in list:
        if x in ret:
            ret.remove(x)
        ret.append(x)
    return ret

def _atd_concat(prefix, list, suffix, env, f=lambda x, env: x):
    """
    Turn list into a string of options, each with the given prefix and suffix,
    except for list members which are not strings, such as Nodes.  This way
    target nodes are concatenated with their full path, without the prefix
    or suffix.
    """
    
    if not list:
        return list

    Debug([prefix, list, suffix])

    if not SCons.Util.is_List(list):
        list = [list]

    def subst(x, env = env):
        if SCons.Util.is_String(x):
            return env.subst(x)
        else:
            return x

    list = map(subst, list)
    Debug(["after subst:"] + list)
    list = f(list,env)
    Debug(["after function:"] + list)
    ret = []

    # ensure that prefix and suffix are strings
    prefix = str(env.subst(prefix))
    suffix = str(env.subst(suffix))

    for x in list:
        # Leave the path without a suffix or prefix if this is a local
        # target node, ie, not a string
        if not isinstance(x, str):
            ret.append (str(x))
            Debug("_atd_concat: appending target node: %s" % str(x))
            continue
        x = str(x)

        if prefix and prefix[-1] == ' ':
            ret.append(prefix[:-1])
            ret.append(x)
        else:
            ret.append(prefix+x)

        if suffix and suffix[0] == ' ':
            ret.append(suffix[1:])
        else:
            ret[-1] = ret[-1]+suffix

    return ret


_global_targets = {}

def _generate (env):
    """Generate the basic eol_scons customizations for the given
    environment, especially applying the scons built-in default tool
    and the eol_scons global tools."""

    GlobalVariables().Update (env)
    if env.has_key('eolsconsdebug') and env['eolsconsdebug']:
        eol_scons.debug = True
    name = env.Dir('.').get_path(env.Dir('#'))
    Debug("Generating eol defaults for Environment(%s) @ %s" % 
          (name, env.Dir('#').get_abspath()))

    # Apply the built-in default tool before applying the eol_scons
    # customizations and tools.
    if env['PLATFORM'] != 'win32':
        import SCons.Tool.default
        SCons.Tool.default.generate(env)
    else:
        import SCons.Tool.mingw
        SCons.Tool.mingw.generate(env)

    # Internal includes need to be setup *before* OptPrefixSetup or any
    # other includes, so that scons will scan for headers locally first.
    # Otherwise it looks in the opt prefix include first, and it notices
    # that the logx headers get installed there (even though not by
    # default).  This creates a dependency on the headers in that location,
    # which causes them to be installed even when the target is not
    # specifically 'install'.  The include arguments *are* (or used to be
    # and may someday again) re-ordered later on the command-line, putting
    # local includes first, but apparently that is not soon enough to
    # affect the scons scan.
    env.PrependUnique (CPPPATH=['#'])

    # Builder wrappers
    Debug("Before wrapping Library, env.Library = %s" % env.Library)
    env.AddMethod(ProgramMethod('Program', env, env.Program), 'Program')
    WrapLibrary("StaticLibrary", env, env.StaticLibrary)
    WrapLibrary("Library", env, env.Library)
    WrapLibrary("SharedLibrary", env, env.SharedLibrary)
    Debug("After wrapping Library, env.Library = %s" % env.Library)

    # Pass on certain environment variables, especially those needed
    # for automatic checkouts.
    env.PassEnv(r'CVS.*|SSH_.*')

    # The global tools will be keyed by directory path, so they will only
    # be applied to Environments contained within that path.  Make the path
    # key absolute since sometimes sub-projects may be out of the current
    # tree.  We also have to store the key in the environment, since later
    # on we may need the key to resolve the global tools, but at that point
    # there is no longer a way to retrieve the directory in which the
    # environment was created.
    global _global_tools
    gkey = env.Dir('.').get_abspath()
    env['GLOBAL_TOOLS_KEY'] = gkey
    if not _global_tools.has_key(gkey):
        _global_tools[gkey] = []

    if env.has_key('GLOBAL_TOOLS'):
        newtools = env['GLOBAL_TOOLS']
        Debug("Adding global tools @ %s: %s" % (gkey, str(newtools)))
        _global_tools[gkey].extend(newtools)
    # Now find every global tool list for parents of this directory.  Sort
    # them so that parent directories will appear before subdirectories.
    dirs = [ k for k in _global_tools.keys() if gkey.startswith(k) ]
    dirs.sort()
    gtools = []
    for k in dirs:
        for t in _global_tools[k]:
            if t not in gtools:
                gtools.append(t)
    Debug("Applying global tools @ %s: %s" %
          (gkey, ",".join([str(x) for x in gtools])))
    env.Require(gtools)
    return env


# ================================================================
# Custom methods for the SCons Environment class.
#
# These are eol_scons internal functions which should only be called as
# methods through an Environment instance.  The methods are added to the
# built-in Environment class directly, so they are available to all
# environment instances once the eol_scons package has been imported.
# Other methods are added to an environment instance only when a particular
# tool has been applied; see prefixoptions.py for an example using 
# InstallLibrary() and related methods.
# ================================================================

def _PassEnv(env, regexp):
    """Pass system environment variables matching regexp to the scons
    execution environment."""
    for ek in os.environ.keys():
        if re.match(regexp, ek):
            env['ENV'][ek] = os.environ[ek]


def _Require(env, tools):
    Debug("eol_scons.Require[%s]" % ",".join([str(x) for x in tools]))
    applied = []
    if not isinstance(tools,type([])):
        tools = [ tools ]
    for t in tools:
        tool = env.Tool(t)
        if tool:
            applied.append( tool )
    return applied


# The following classes create a call chain with an existing builder,
# replacing that builder's call method with the one from the wrapper
# instance.  All other attributes of the existing builder need to be
# preserved, thus these don't replace the existing builder, only the
# builder's __call__ method.

class ProgramMethod:
    """
    Wrap the Program builder to add the targets as a named construction
    variable, by which other parts of the build can refer to them.
    """

    def __init__(self, name, env, method):
        self.name = name
        self.method = method
        if not env.has_key('EXTRA_SOURCES'):
            env['EXTRA_SOURCES'] = []
        Debug("created Program wrapper, method=%s" % (self.method))

    def __call__(self, env, target = None, source = _null, **overrides):
        Debug("called Program wrapper, method=%s" %
              (self.method))
        es = env['EXTRA_SOURCES']
        if source == _null and len(es) == 0:
            return self.method(target, source, **overrides)
        else:
            if type(source) != type([]):
                source = [source]
            return self.method(target, source + es, **overrides)


def WrapLibrary(name, env, method):
    env.AddMethod(LibraryMethod(name, env, method), name)


class LibraryMethod:
    """
    Wrap a Library Environment method to add the resulting library target
    as a named global target.  Other parts of the build can refer to these
    named targets implicitly by using AppendLibrary() or explicitly through
    GetGlobalTarget().

    Typically the environment method being wrapped is actually a
    SCons.Environment.BuilderWrapper, so this effectively chains that
    MethodWrapper with this one.  Since the existing MethodWrapper is
    already bound to the Environment instance, the environment does not
    need to be passed when the chained method is called.
    """

    def __init__(self, name, env, method):
        self.name = name
        self.library = method
        Debug("created library wrapper for %s, library=%s" %
              (name, self.library))

    def __call__(self, env, target = None, source = _null, **overrides):
        "Add the library to the list of global targets."
        Debug("called library wrapper for %s" % self.name)
        ret = self.library(target, source, **overrides)
        if target:
            env.AddLibraryTarget(target, ret)
        return ret


def _Test (self, sources, actions):
    """Create a test target and aliases for the given actions with
    sources as its dependencies.

    Tests within a particular directory can be run using the xtest name, as
    in 'scons datastore/tests/xtest', or 'scons -u xtest' to run the tests
    for the current directory.  Tests created with this method will also be
    added to the global 'test' alias."""
    xtest = self.Command("xtest", sources, actions)
    self.Precious(xtest)
    self.AlwaysBuild(xtest)
    DefaultEnvironment().Alias('test', xtest)
    return xtest


def _ChdirActions (self, actions, dir = None):
    return chdir.ChdirActions(self, actions, dir)

def _Install (self, dir, source):
    """Call the standard Install() method and also add the target to the
    global 'install' alias."""
    t = SCons.Environment.Base.Install (self, dir, source)
    DefaultEnvironment().Alias('install', t)
    return t

def _ExtraSources(env, source):
    """Add the given list of sources to the list of extra sources.

    If a member of the source list is a string, then it will be resolved
    to a target from the list of global targets.  Otherwise the members
    must be a SCons target node.
    """
    if type(source) != type([]):
        source = [source]
    targets=[]
    for s in source:
        try:
            if type(s) == str:
                targets.append (_global_targets[s])
            else:
                targets.append (s)
        except KeyError:
            print "Unknown global target '%s'." % (s)
    env['EXTRA_SOURCES'].extend (targets)
    return targets

def _AddLibraryTarget(env, base, target):
    "Register this library target using a prefix reserved for libraries."
    while type(base) == type(NodeList) or type(base) == type([]):
        base = base[0]
    name = "lib"+str(base)
    env.AddGlobalTarget(name, target)
    return target
    
def _AddGlobalTarget(env, name, target):
    "Register this target under the given name."
    # Make sure we register a node and not a list, just because that has
    # been the convention, started before scons changed all targets to
    # lists.
    # If the target already exists, then do not change it, so the first
    # setting always takes precedence.
    try:
        node = target[0]
    except (TypeError, AttributeError):
        node = target
    if not _global_targets.has_key(name):
        Debug("AddGlobalTarget: " + name + "=" + node.get_abspath())
        _global_targets[name] = node
    else:
        Debug(("%s global target already set to %s, " +
               "not changed to %s.") % (name, _global_targets[name], 
                                        node.get_abspath()))
    # The "local" targets is a dictionary of target strings mapped to their
    # node.  The dictionary is assigned to a construction variable.  That
    # way anything can be used as a key, while environment construction
    # keys have restrictions on what they can contain.
    if not env.has_key("LOCAL_TARGETS"):
        env["LOCAL_TARGETS"] = {}
    locals = env["LOCAL_TARGETS"]
    if not locals.has_key(name):
        Debug("local target: " + name + "=" + str(node))
        locals[name] = node
    else:
        Debug(("%s local target already set to %s, " +
               "not changed to %s.") % (name, locals[name], node))
    return node


def _GetGlobalTarget(env, name):
    "Look up a global target node by this name and return it."
    # If the target exists in the local environment targets, use that one,
    # otherwise resort to the global dictionary.
    try:
        return env["LOCAL_TARGETS"][name]
    except KeyError:
        pass
    try:
        return _global_targets[name]
    except KeyError:
        pass
    return None


def _AppendLibrary (env, name, path = None):
    "Add this library either as a local target or a link option."
    Debug("AppendLibrary wrapper looking for %s" % name)
    env.Append(DEPLOY_SHARED_LIBS=[name])
    target = env.GetGlobalTarget("lib"+name)
    if target:
        Debug("appending library node: %s" % str(target))
        env.Append(LIBS=[target])
    else:
        env.Append(LIBS=[name])
        if path:
            env.Append(LIBPATH=[path])

def _AppendSharedLibrary (env, name, path=None):
    "Add this shared library either as a local target or a link option."
    env.Append(DEPLOY_SHARED_LIBS=[name])
    target = env.GetGlobalTarget("lib"+name)
    Debug("appending shared library node: %s" % str(target))
    if target and not path:
        path = target.dir.get_abspath()
    env.Append(LIBS=[name])
    if not path:
        return
    env.AppendUnique(LIBPATH=[path])
    env.AppendUnique(RPATH=[path])

def _FindPackagePath(env, optvar, globspec, defaultpath = None):
    """Check for a package installation path matching globspec."""
    options = GlobalVariables()
    dir=defaultpath
    try:
        dir=os.environ[optvar]
    except KeyError:
        if not env:
            env = DefaultEnvironment()
        options.Update(env)
        dirs = glob.glob(env.subst(globspec))
        dirs.sort()
        dirs.reverse()
        for d in dirs:
            if os.path.isdir(d):
                dir=d
                break
    return dir


# This is for backwards compatibility only to help with transition.
# Someday it will be removed.
def _Create (env,
            package,
            platform=None,
            tools=None,
            toolpath=None,
            options=None,
            **kw):
    return Environment (platform, tools, toolpath, options, **kw)


def _LogDebug(env, msg):
    Debug(msg)

def _GlobalVariables(env):
    return GlobalVariables()

def _GlobalTools(env):
    global _global_tools
    gkey = env.get('GLOBAL_TOOLS_KEY')
    gtools = None
    if gkey and _global_tools.has_key(gkey):
        gtools = _global_tools[gkey]
    Debug("GlobalTools(%s) returns: %s" % (gkey, gtools))
    return gtools


tool_matches = None

def _findToolFile(env, name):
    global tool_matches
    if tool_matches == None:
        # Get a list of all files named "tool_<tool>.py" under the
        # top directory.
        toolpattern = re.compile("^tool_.*\.py")
        def addMatches(matchList, dirname, contents):
            matchList.extend([os.path.join(dirname, file) 
                              for file in
                              filter(toolpattern.match, contents)])
            if '.svn' in contents:
                contents.remove('.svn')
        tool_matches = []
        os.path.walk(env.Dir('#').get_abspath(), addMatches, tool_matches)

    toolFileName = "tool_" + name + ".py"
    return filter(lambda f: toolFileName == os.path.basename(f), tool_matches)


def _loadToolFile(env, name):
    # See if there's a file named "tool_<tool>.py" somewhere under the
    # top directory.  If we find one, load it as a SConscript which 
    # should define and export the tool.
    tool = None
    matchList = _findToolFile(env, name)
    # If we got a match, load it
    if (len(matchList) > 0):
        # If we got more than one match, complain...
        if (len(matchList) > 1):
            print("Warning: multiple tool files for " + name + ": " + 
                  str(matchList) + ", using the first one")
        # Load the first match
        toolScript = matchList[0]
        Debug("Loading %s to get tool %s..." % (toolScript, name))
        env.SConscript(toolScript)
        # After loading the script, make sure the tool appeared 
        # in the global exports list.
        if global_exports.has_key(name):
            tool = global_exports[name]
        else:
            raise SCons.Errors.StopError, "Tool error: " + \
                toolScript + " does not export symbol '" + name + "'"
    return tool


# This serves as a cache for certain kinds of tools which only need to be
# loaded and instantiated once.  The name is mapped to the resolved python
# function.  For example, tool_<name>.py files only need to be loaded once
# to define the tool function, likewise for other exported tool functions.
# However, tool.py modules with keyword parameters need to be instantiated
# every time, since the instances may be specialized by different keyword
# dictionaries.  Most of the tools in eol_scons site_tools expect to be
# loaded only once, and since those tools are not loaded with keywords,
# they are still cached in the tool dictionary as before.
tool_dict = {}

def _Tool(env, tool, toolpath=None, **kw):
    Debug("eol_scons.Tool(%s,%s,kw=%s)" % (env.Dir('.'), tool, str(kw)))
    name = str(tool)
    if SCons.Util.is_String(tool):
        name = env.subst(tool)
        tool = None
        
        # The canonical name we use for a tool is all lower case, with
        # any leading PKG_ stripped off...
        name = name.strip().replace("PKG_", "", 1).lower()

        # Is the tool already in our tool dictionary?
        if tool_dict.has_key(name):
            Debug("Found tool %s already loaded" % name)
            if not kw:
                tool = tool_dict[name]
            else:
                Debug("Existing tool not used because keywords were given.")

        # Check if this tool is actually an exported tool function, in
        # which case return the exported function.  First check for the
        # tool under the given name.  For historical reasons, we look also
        # look for the tool with:
        #    o the canonical name
        #    o canonical name converted to upper case, with PKG_ prepended
        #      if not already there
        if not tool:
            pkgName = "PKG_" +  name.upper()
            for tname in [name, pkgName]:
                if global_exports.has_key(tname):
                    tool = global_exports[tname]
                    break

            if tool:
                Debug("Found tool %s in global_exports (as %s)" % (name, tname))

        # Try to find and load a tool file named "tool_<tool>.py".
        if not tool:
            tool = _loadToolFile(env, name)

        # All tool functions found above can be stashed safely in the tool
        # dictionary for future reference.  That's true even if keyword
        # parameters were passed, because these tools are python functions
        # and the keywords will not be used anywhere.
        if tool:
            tool_dict[name] = tool

        # Still nothing?  Resort to the usual SCons tool behavior.  This
        # section tries to duplicate the functionality in
        # SCons.Environment.Environment.Tool(), except we don't want to
        # actually apply the tool yet and we want to be able to return the
        # tool, neither of which we can do by calling the default Tool()
        # method.  If this last resort fails, then there should be an
        # exception which will propagate up from here.  This tool instance
        # is *not* stashed in the local tool dictionary if there are
        # keyword parameters.
        if not tool:
            Debug("Loading tool: %s" % name)
            if toolpath is None:
                toolpath = env.get('toolpath', [])
            toolpath = map(env._find_toolpath_dir, toolpath)
            tool = apply(SCons.Tool.Tool, (name, toolpath), kw)
            Debug("Tool loaded: %s" % name)
            # If the tool is not specialized with keywords, then we can 
            # stash this particular instance and avoid reloading it.
            if tool and not kw:
                tool_dict[name] = tool
            elif kw:
                Debug("Tool %s not cached because it has keyword parameters."
                      % (name))

    Debug("Applying tool %s" % name)
    tool(env)
    return tool


def _SetHelp(env, text):
    """
    Override the SConsEnvironment Help method to first erase any previous
    help text.  This can help if multiple SConstruct files in a project
    each try to generate the help text all at once.
    """
    import SCons.Script
    SCons.Script.help_text = None
    env._SConscript_Help(text)


# Include this as a standard part of Environment, so that other tools can
# conveniently add their doxref without requiring the doxygen tool.
def _AppendDoxref(env, ref):
    """Append to the DOXREF variable and force it to be a list."""
    if not env.has_key('DOXREF'):
        env['DOXREF'] = [ref]
    else:
        env['DOXREF'].append(ref)
    Debug("Appended %s; DOXREF=%s" % (ref, str(env['DOXREF'])))


def _ExtendEnvironment(envclass):
    
    envclass.Require = _Require
    envclass.ExtraSources = _ExtraSources
    envclass.AddLibraryTarget = _AddLibraryTarget
    envclass.AddGlobalTarget = _AddGlobalTarget
    envclass.GetGlobalTarget = _GetGlobalTarget
    envclass.AppendLibrary = _AppendLibrary
    envclass.AppendSharedLibrary = _AppendSharedLibrary
    envclass.PassEnv = _PassEnv
    envclass.Install = _Install
    envclass.ChdirActions = _ChdirActions
    envclass.Test = _Test
    envclass.LogDebug = _LogDebug
    envclass.FindPackagePath = _FindPackagePath
    envclass.GlobalVariables = _GlobalVariables
    # Alias for temporary backwards compatibility
    envclass.GlobalOptions = _GlobalVariables
    envclass.GlobalTools = _GlobalTools
    envclass.Tool = _Tool
    envclass.AppendDoxref = _AppendDoxref

    # So that only the last Help text setting takes effect, rather than
    # duplicating info when SConstruct files are loaded from sub-projects.
    envclass._SConscript_Help = envclass.Help
    envclass.SetHelp = _SetHelp

    # For backwards compatibility:
    envclass.Create = _Create

_ExtendEnvironment(SCons.Environment.Environment)

# ================================================================
# End of Environment customization.
# ================================================================

Debug("eol_scons.__init__ loaded.")
