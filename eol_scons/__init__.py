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
import SCons.Variables

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
_enable_cache = False

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
        global_variables.AddVariables(
            BoolVariable('eolsconscache',
                         'Enable tools.cache optimization.',
                         _enable_cache))
        print "Config files: %s" % (global_variables.files)
    return global_variables

# Alias for temporary backwards compatibility
GlobalOptions = GlobalVariables

_cache_variables = None


class VariableCache(SCons.Variables.Variables):

    def __init__(self, path):
        SCons.Variables.Variables.__init__(self, path)
        self.cfile = path

    def getPath(self):
        return self.cfile

    def cacheKey(self, name):
        return "_vcache_" + name

    def lookup(self, env, name):
        key = self.cacheKey(name)
        if not key in self.keys():
            self.Add(key)
        self.Update(env)
        value = None
        if env.has_key(key):
            value = env[key]
            Debug("returning %s cached value: %s" % (key, value))
        else:
            Debug("no value cached for %s" % (key))
        return value
        
    def store(self, env, name, value):
        # Update the cache
        key = self.cacheKey(name)
        env[key] = value
        if self.getPath():
            self.Save(self.getPath(), env)
        Debug("Updated %s to value %s" % (key, value))


def ToolCacheVariables():
    global _cache_variables
    if not _cache_variables:
        global debug
        global _enable_cache
        Debug("creating _cache_variables: eolsconsdebug=%s, eolsconscache=%s" %
              (debug, _enable_cache))
        cfile = "tools.cache"
        if not cfile.startswith("/"):
            # Turn relative config file path to absolute, relative
            # to top directory.
            cfile = os.path.abspath(os.path.join(__path__[0], 
                                                 "../..", cfile))
        if _enable_cache:
            _cache_variables = VariableCache (cfile)
            print("Tool settings cache: %s" % (_cache_variables.getPath()))
        else:
            _cache_variables = VariableCache (None)
            print("Tool cache will not be used.  (It is now disabled by default.)  "
                  "It can be enabled by setting eolsconscache=1")
    return _cache_variables


def PathToAbsolute(path, env):
    "Convert a Path variable to an absolute path relative to top directory."
    apath = env.Dir('#').Dir(path).get_abspath()
    # print("Converting PREFIX=%s to %s" % (path, apath))
    return apath


# ================================================================
# End of public interface
# ================================================================

_global_tools = {}

_global_targets = {}

from SCons.Builder import BuilderBase

class _LibraryBuilder(BuilderBase):
    """
    This class should allow for equivalent instances to the builder created
    by SCons.Tool.createStaticLibBuilder, as long as the right Builder
    keywords are propagated to the BuilderBase subclass.  The only
    difference in the subclass instance should be the __call__ method to
    intercept the library target.
    """

    def __init__(self, builder):
        BuilderBase.__init__(self, 
                             action = builder.action,
                             emitter = builder.emitter,
                             prefix = builder.prefix,
                             suffix = builder.suffix,
                             src_suffix = builder.src_suffix,
                             src_builder = builder.src_builder)

    def __call__(self, env, target=None, source=None, chdir=_null, **kw):
        "Override __call__ from the base class to register the target library."
        Debug("_LibraryBuilder.__call__ for target(%s)" % (target))
        ret = BuilderBase.__call__(self, env, target, source, chdir, **kw)
        if target:
            env.AddLibraryTarget(target, ret)
        else:
            Debug("library builder returned None!")
        return ret

def _library_builder_str(env):
    t = "[env.Library=%s, builder=%s]"
    try:
        libmethod = env.Library
    except AttributeError:
        libmethod = "None"
    return t % (libmethod, env.get_builder('Library'))

_default_tool_list = None

# The first attempt by scons to build DefaultEnvironment will load the
# eol_scons default tool, which can cause things like infinite recursion if
# a tool causes the DefaultEnvironment() call.  To try to cut that off,
# create the default environment here, but without any of the eol_scons
# extensions.

_scons_default_environment = None
_creating_default_environment = False

def _createDefaultEnvironment():

    global _scons_default_environment
    global _creating_default_environment
    if (not _scons_default_environment and
        not _creating_default_environment):
        _creating_default_environment = True
        _scons_default_environment = SCons.Defaults.DefaultEnvironment()
        _creating_default_environment = False


def _update_variables(env):
    GlobalVariables().Update (env)
    if env.has_key('eolsconsdebug'):
        eol_scons.debug = env['eolsconsdebug']
    if env.has_key('eolsconscache'):
        eol_scons._enable_cache = env['eolsconscache']


def _generate (env):
    """Generate the basic eol_scons customizations for the given
    environment, especially applying the scons built-in default tool
    and the eol_scons global tools."""
    _createDefaultEnvironment()
    _update_variables(env)
    name = env.Dir('.').get_path(env.Dir('#'))
    Debug("Generating eol defaults for Environment(%s) @ %s" % 
          (name, env.Dir('#').get_abspath()))

    # Apply the built-in default tool before applying the eol_scons
    # customizations and tools.  We only need to find the tools once, so
    # subvert the SCons.Tool.default.generate(env) implementation with our
    # own implementation here.  First time through, accumulate the default
    # list of tool names, cache it for the next time around, and stash the
    # list of instantiated default tools.  We can cache the names returned
    # by tool_list in tools.cache, and then we can create the Tool()
    # instances for those names and store them in a local variable for
    # re-use on each new Environment.

    global _default_tool_list
    if _default_tool_list == None:

        # See if the default list of tool names is already in the cache
        cache = env.CacheVariables()
        key = "_eol_scons_default_tool_names"
        toolnames = cache.lookup(env, key)
        if not toolnames:
            if env['PLATFORM'] != 'win32':
                toolnames = SCons.Tool.tool_list(env['PLATFORM'], env)
            else:
                toolnames = ['mingw']
            cache.store(env, key, "\n".join(toolnames))
        else:
            toolnames = toolnames.split("\n")

        # Now instantiate a Tool for each of the names.
        _default_tool_list = [ SCons.Tool.Tool(t) for t in toolnames ]

    # Now apply the default tools
    for tool in _default_tool_list:
        tool(env)

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

    # The customized Library wrapper methods might be added directly to
    # envclass, as in _ExtendEnvironment, except SCons overrides the
    # instance methods associated with builders, so I don't think that
    # would work.  It should work to "chain" MethodWrapper, by calling
    # AddMethod() to add a function object which then calls the original
    # MethodWrapper instance.  However, this runs into problems with
    # Environment.Clone().  When the Environment Builders are cloned, they
    # are added back to the BUILDERS dictionary, and that dictionary is
    # especially designed to update the Environment instance methods
    # corresponding to the Builders.  Maybe that's as it should be, but the
    # point is that we need to replace the standard builder with our own
    # copy of the builder.
    #
    # Can the global list of targets be acquired other than by intercepting
    # Library() just to register the global targets?  Perhaps when
    # GetGlobalTarget is called, it can search the SCons Node tree for a
    # target which matches that name?  That would be supremely simpler, as
    # long as the tree search is not too slow.  One problem may be
    # selecting among multiple nodes with similar names.  Which is the one
    # to which the wrapped Library call would have pointed?

    # Debug("Before wrapping Library: %s" % (_library_builder_str(env)))

    Debug("Replacing standard library builders with subclass")
    builder = SCons.Tool.createStaticLibBuilder(env)
    builder = _LibraryBuilder(builder)
    env['BUILDERS']['StaticLibrary'] = builder
    env['BUILDERS']['Library'] = builder
    builder = SCons.Tool.createSharedLibBuilder(env)
    builder = _LibraryBuilder(builder)
    env['BUILDERS']['SharedLibrary'] = builder

    # Debug("After wrapping Library: %s" % (_library_builder_str(env)))

    # Pass on certain environment variables, especially those needed
    # for automatic checkouts.
    env.PassEnv(r'CVS.*|SSH_.*')

    if _creating_default_environment:
        print("Limiting DefaultEnvironment to standard scons tools.")
        return env

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
    applied = []
    if not isinstance(tools,type([])):
        tools = [ tools ]
    Debug("eol_scons.Require[%s]" % ",".join([str(x) for x in tools]))
    for t in tools:
        tool = env.Tool(t)
        if tool:
            applied.append( tool )
    return applied


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

def _CacheVariables(env):
    return ToolCacheVariables()

def _GlobalTools(env):
    global _global_tools
    gkey = env.get('GLOBAL_TOOLS_KEY')
    gtools = None
    if gkey and _global_tools.has_key(gkey):
        gtools = _global_tools[gkey]
    Debug("GlobalTools(%s) returns: %s" % (gkey, gtools))
    return gtools


_tool_matches = None

def _findToolFile(env, name):
    global _tool_matches
    # Need to know if the cache is enabled or not.
    _update_variables(env)
    cache = ToolCacheVariables()
    toolcache = cache.getPath()
    if _tool_matches == None:
        cvalue = cache.lookup(env, '_tool_matches')
        if cvalue:
            _tool_matches = cvalue.split("\n")
            print("Using %d cached tool filenames from %s" % 
                  (len(_tool_matches), toolcache))

    if _tool_matches == None:
        print("Searching for tool_*.py files...")
        # Get a list of all files named "tool_<tool>.py" under the
        # top directory.
        toolpattern = re.compile("^tool_.*\.py")
        def addMatches(matchList, dirname, contents):
            matchList.extend([os.path.join(dirname, file) 
                              for file in
                              filter(toolpattern.match, contents)])
            if '.svn' in contents:
                contents.remove('.svn')
            if 'site_scons' in contents:
                contents.remove('site_scons')
            if 'apidocs' in contents:
                contents.remove('apidocs')
        _tool_matches = []
        os.path.walk(env.Dir('#').get_abspath(), addMatches, _tool_matches)
        # Update the cache
        cache.store(env, '_tool_matches', "\n".join(_tool_matches))
        print("Found %d tool files in source tree, cached in %s" %
              (len(_tool_matches), toolcache))

    toolFileName = "tool_" + name + ".py"
    return filter(lambda f: toolFileName == os.path.basename(f), _tool_matches)


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
    # Debug("...before loading tool %s: %s" % (name, _library_builder_str(env)))

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
    # Debug("...after applying tool %s: %s" % (name, _library_builder_str(env)))
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
    # If the reference is a Doxygen target node, convert it into a
    # directory reference by stripping the html/index.html from it.
    if type(ref) != type(""):
        ref = ref.Dir('..').name
    if not env.has_key('DOXREF'):
        env['DOXREF'] = [ref]
    else:
        env['DOXREF'].append(ref)
    Debug("Appended %s; DOXREF=%s" % (ref, str(env['DOXREF'])))


def _ExtendEnvironment(envclass):
    
    envclass.Require = _Require
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
    envclass.CacheVariables = _CacheVariables
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
