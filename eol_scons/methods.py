# -*- python -*-
# Copyright 2007 UCAR, NCAR, All Rights Reserved

import os, re, glob

import SCons.Util
from SCons.Util import NodeList
from SCons.Script import DefaultEnvironment

from SCons.Script.SConscript import global_exports

import variables as es_vars
import tool as es_tool
import eol_scons.debug as esd
import chdir

_global_targets = {}
_tool_matches = None

""" Custom methods for the SCons Environment class.

    These are eol_scons internal functions which should only be called as
    methods through an Environment instance.  The methods are added to the
    built-in Environment class directly, so they are available to all
    environment instances once the eol_scons package has been imported.
    Other methods are added to an environment instance only when a particular
    tool has been applied; see prefixoptions.py for an example using 
    InstallLibrary() and related methods.
"""


def _PassEnv(env, regexp):
    """Pass system environment variables matching regexp to the scons
    execution environment."""
    for ek in os.environ.keys():
        if re.match(regexp, ek):
            env['ENV'][ek] = os.environ[ek]

def _Require(env, tools):
    applied = []
    if not isinstance(tools, type([])):
        tools = [tools]
    env.LogDebug("eol_scons.Require[%s]" % ",".join([str(x) for x in tools]))
    for t in tools:
        tool = env.Tool(t)
        if tool:
            applied.append(tool)
    return applied


def _Test(self, sources, actions):
    """Create a test target and aliases for the given actions with
    sources as its dependencies.

    Tests within a particular directory can be run using the xtest name, as
    in 'scons datastore/tests/xtest', or 'scons -u xtest' to run all the
    tests with the alias xtest, or 'scons test' to run all default
    tests."""
    # This implementation has been moved into a separate testing tool.
    self.Tool("testing")
    return self.DefaultTest(self.TestRun("xtest", sources, actions))

def _ChdirActions(self, actions, cdir=None):
    return chdir.ChdirActions(self, actions, cdir)

def _Install(self, ddir, source):
    """Call the standard Install() method and also add the target to the
    global 'install' alias."""
    t = self._SConscript_Install(self.Dir(ddir), source)
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
    except(TypeError, AttributeError):
        node = target
    if not _global_targets.has_key(name):
        env.LogDebug("AddGlobalTarget: " + name + "=" + node.get_abspath())
        _global_targets[name] = node
    else:
        env.LogDebug(("%s global target already set to %s, " +
                      "not changed to %s.") % (name, _global_targets[name], 
                                               node.get_abspath()))
    # The "local" targets is a dictionary of target strings mapped to their
    # node.  The dictionary is assigned to a construction variable.  That
    # way anything can be used as a key, while environment construction
    # keys have restrictions on what they can contain.
    if not env.has_key("LOCAL_TARGETS"):
        env["LOCAL_TARGETS"] = {}
    local_tgts = env["LOCAL_TARGETS"]
    if not local_tgts.has_key(name):
        env.LogDebug("local target: " + name + "=" + str(node))
        local_tgts[name] = node
    else:
        env.LogDebug(("%s local target already set to %s, " +
                      "not changed to %s.") % (name, local_tgts[name], node))
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


def _AppendLibrary(env, name, path=None):
    "Add this library either as a local target or a link option."
    env.LogDebug("AppendLibrary wrapper looking for %s" % name)
    env.Append(DEPLOY_SHARED_LIBS=[name])
    target = env.GetGlobalTarget("lib"+name)
    if target:
        env.LogDebug("appending library node: %s" % str(target))
        env.Append(LIBS=[target])
    else:
        env.Append(LIBS=[name])
        if path:
            env.Append(LIBPATH=[path])

def _AppendSharedLibrary(env, name, path=None):
    "Add this shared library either as a local target or a link option."
    env.Append(DEPLOY_SHARED_LIBS=[name])
    target = env.GetGlobalTarget("lib"+name)
    env.LogDebug("appending shared library node: %s" % str(target))
    if target and not path:
        path = target.dir.get_abspath()
    env.Append(LIBS=[name])
    if not path:
        return
    env.AppendUnique(LIBPATH=[path])
    env.AppendUnique(RPATH=[path])

def _FindPackagePath(env, optvar, globspec, defaultpath=None):
    """Check for a package installation path matching globspec."""
    options = es_vars.GlobalVariables()
    pdir = defaultpath
    try:
        pdir = os.environ[optvar]
    except KeyError:
        if not env:
            env = DefaultEnvironment()
        options.Update(env)
        dirs = glob.glob(env.subst(globspec))
        dirs.sort()
        dirs.reverse()
        for d in dirs:
            if os.path.isdir(d):
                pdir = d
                break
    return pdir


# This is for backwards compatibility only to help with transition.
# Someday it will be removed.
def _Create(env,
            package,
            platform=None,
            tools=None,
            toolpath=None,
            options=None,
            **kw):
    return Environment(platform, tools, toolpath, options, **kw)


def _LogDebug(env, msg):
    esd.Debug(msg, env)

def _GlobalVariables(env, cfile=None):
    return es_vars.GlobalVariables(cfile, env)

def _CacheVariables(env):
    return es_vars.ToolCacheVariables(env)

def _GlobalTools(env):
    gkey = env.get('GLOBAL_TOOLS_KEY')
    gtools = None
    if gkey and es_tool._global_tools.has_key(gkey):
        gtools = es_tool._global_tools[gkey]
    env.LogDebug("GlobalTools(%s) returns: %s" % (gkey, gtools))
    return gtools


def _findToolFile(env, name):
    global _tool_matches
    # Need to know if the cache is enabled or not.
    es_vars._update_variables(env)
    cache = es_vars.ToolCacheVariables(env)
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
        toolpattern = re.compile(r"^tool_.*\.py")
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
        env.LogDebug("Loading %s to get tool %s..." % (toolScript, name))
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
    env.LogDebug("eol_scons.Tool(%s,%s,kw=%s)" % (env.Dir('.'), tool, str(kw)))
    name = str(tool)
    env.LogDebug("...before applying tool %s: %s" % (name, esd.Watches(env)))

    if SCons.Util.is_String(tool):
        name = env.subst(tool)
        tool = None
        
        # Is the tool already in our tool dictionary?
        if tool_dict.has_key(name):
            env.LogDebug("Found tool %s already loaded" % name)
            if not kw:
                tool = tool_dict[name]
            else:
                env.LogDebug("Existing tool not used because "
                             "keywords were given.")

        # Check if this tool is actually an exported tool function.
        if not tool:
            tool = global_exports.get(name)
            if tool:
                env.LogDebug("Found tool %s in global_exports" % (name))

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
            env.LogDebug("Loading tool: %s" % name)
            if toolpath is None:
                toolpath = env.get('toolpath', [])
            toolpath = map(env._find_toolpath_dir, toolpath)
            tool = apply(SCons.Tool.Tool, (name, toolpath), kw)
            env.LogDebug("Tool loaded: %s" % name)
            # If the tool is not specialized with keywords, then we can 
            # stash this particular instance and avoid reloading it.
            if tool and not kw:
                tool_dict[name] = tool
            elif kw:
                env.LogDebug("Tool %s not cached because it has "
                             "keyword parameters." % (name))

    env.LogDebug("Applying tool %s" % name)
    tool(env)
    env.LogDebug("...after applying tool %s: %s" % (name, esd.Watches(env)))
    # We could regenerate the help text after each tool is loaded,
    # presuming that only tools add variables, but that would not catch
    # variables which are added after the last tool is loaded, as well as
    # being a lot of extra calls.  So this works to a point, and it would
    # still allow the help text to be customized at the end of the
    # SConstruct file (unlike wrapping the _SConscript call below).
    # However, it is left unused in favor of adding a simple SetHelp() call
    # at the end of SConstruct.
    #
    # env.SetHelp()
    #
    return tool

def _SConscript(fs, *files, **kw):
    # This is a custom wrapper to the SCons function which reads a
    # SConscript file (including the SConstruct file).  Set the help text
    # after the last SConscript has been read.  However this approach
    # doesn't work, because the _SConscript() function makes some
    # assumptions about the call stack, and so I think inserting this
    # function in the stack causes problems.
    _real_SConscript(fs, *files, **kw)
    if SCons.Script.sconscript_reading == 0:
        env = DefaultEnvironment()
        env.SetHelp()

if False:
    _real_SConscript = SCons.Script._SConscript._SConscript
    SCons.Script._SConscript._SConscript = _SConscript

def _SetHelp(env, text=None):
    """
    Override the SConsEnvironment Help method to first erase any previous
    help text.  This can help if multiple SConstruct files in a project
    each try to generate the help text all at once.  If @p text is None,
    then generate the help text from the global variables.  To clear the
    help text to an empty string, pass "" in @p text.
    """
    import SCons.Script
    SCons.Script.help_text = None
    if text is None:
        variables = env.GlobalVariables()
        variables.Update(env)
        text = variables.GenerateHelpText(env)

    # It doesn't work to call the real Help() function because it performs
    # a substitution on the text.  There is already lots of variable help
    # text written using $VARIABLE which is not supposed to be substituted.
    # Further, some of the $VARIABLE references do not parse because they
    # are followed by a period. (eg, soqt.py and coin.py) So instead call
    # the HelpFunction() directly.  If that ever breaks and we need to
    # resort to calling the standard Help() method, then it may help to fix
    # the variable references in the help text first, like so:
    #
    # text = re.sub(r'\$', '$$', text)
    # env.Help(text)
    #
    SCons.Script.HelpFunction(text)


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
    env.LogDebug("Appended %s; DOXREF=%s" % (ref, str(env['DOXREF'])))


def _addMethods(env):
    
    if hasattr(env, "_SConscript_Install"):
        env.LogDebug("environment %s already has methods added" % (env))
        return
    env.AddMethod(_LogDebug, "LogDebug")
    env.LogDebug("add methods to environment %s, Install=%s, new _Install=%s" % 
                 (env, env.Install, _Install))
    env.AddMethod(_Require, "Require")
    env.AddMethod(_AddLibraryTarget, "AddLibraryTarget")
    env.AddMethod(_AddGlobalTarget, "AddGlobalTarget")
    env.AddMethod(_GetGlobalTarget, "GetGlobalTarget")
    env.AddMethod(_AppendLibrary, "AppendLibrary")
    env.AddMethod(_AppendSharedLibrary, "AppendSharedLibrary")
    env.AddMethod(_PassEnv, "PassEnv")
    env._SConscript_Install = env.Install
    env.AddMethod(_Install, "Install")
    env.AddMethod(_ChdirActions, "ChdirActions")
    env.AddMethod(_Test, "Test")
    env.AddMethod(_FindPackagePath, "FindPackagePath")
    env.AddMethod(_GlobalVariables, "GlobalVariables")
    env.AddMethod(_CacheVariables, "CacheVariables")
    # Alias for temporary backwards compatibility
    env.AddMethod(_GlobalVariables, "GlobalOptions")
    env.AddMethod(_GlobalTools, "GlobalTools")
    env.AddMethod(_Tool, "Tool")
    env.AddMethod(_AppendDoxref, "AppendDoxref")

    # So that only the last Help text setting takes effect, rather than
    # duplicating info when SConstruct files are loaded from sub-projects.
    env.AddMethod(_SetHelp, "SetHelp")

    # For backwards compatibility:
    env.AddMethod(_Create, "Create")

