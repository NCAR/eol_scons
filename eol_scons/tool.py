# -*- python -*-
# Copyright 2007 UCAR, NCAR, All Rights Reserved

"""
Tool methods invoked when tools/eol_scons.py or hooks/default.py are
loaded as a tool.  This module is not actually a scons tool, it is just the
functionality which applies the eol_scons extensions as if it were a tool.
"""

import os
import re
import SCons.Tool

from eol_scons import Debug

from SCons.Script.SConscript import global_exports

import eol_scons.library
import eol_scons.methods
import eol_scons.variables as esv
import eol_scons.debug as esd

_tool_matches = None
_global_tools = {}

def _setup_global_tools(env):
    """
    Make sure the global tools list exists for this Environment.  Generate
    the key and make sure an entry for that key exists in the _global_tools
    map.  Return the key.
    """
    gkey = env.get('GLOBAL_TOOLS_KEY')
    if not gkey:
        gkey = env.Dir('.').get_abspath()
        env['GLOBAL_TOOLS_KEY'] = gkey
    if gkey not in _global_tools:
        _global_tools[gkey] = []
    return gkey


def _apply_global_tools(env):
    """
    The global tools are keyed by directory path, so they are only applied
    to Environments contained within that path.  The path key is absolute
    since sometimes sub-projects may be out of the current tree.  We also
    have to store the key in the environment, since later on we may need
    the key to resolve the global tools, but at that point there is no
    longer a way to retrieve the directory in which the environment was
    created.
    """
    gkey = _setup_global_tools(env)
    env.LogDebug("Entering apply_global_tools with key %s" % (gkey))

    if 'GLOBAL_TOOLS' in env:
        newtools = env['GLOBAL_TOOLS']
        env.LogDebug("Adding global tools @ %s: %s" % (gkey, str(newtools)))
        _global_tools[gkey].extend(newtools)
    # Now find every global tool list for parents of this directory.  Sort
    # them so that parent directories will appear before subdirectories.
    dirs = [k for k in _global_tools.keys() if gkey.startswith(k)]
    dirs.sort()
    gtools = []
    for k in dirs:
        for t in _global_tools[k]:
            if t not in gtools:
                gtools.append(t)
    env.LogDebug("Applying global tools @ %s: %s" %
                 (gkey, ",".join([str(x) for x in gtools])))
    env.Require(gtools)


def _GlobalTools(env):
    """
    Return the list of global tools for this Environment.  To preserve past
    behavior, in case anything depends on it, this method specifically does
    not setup the global tools if they do not exist yet in this
    Environment.  Instead, it returns None.
    """
    gkey = env.get('GLOBAL_TOOLS_KEY')
    gtools = None
    if gkey and gkey in _global_tools:
        gtools = _global_tools[gkey]
    env.LogDebug("GlobalTools(%s) returns: %s" % (gkey, gtools))
    return gtools


def _RequireGlobal(env, tools):
    """
    Add the tool(s) to the global tools list and apply them to the
    environment.  This is just like the Require() method, except for also
    adding the tools to the global tools list.  This method assumes that
    any other global tools, whether inherited from parent directories or
    previously added to this Environment, have already been applied.
    """
    if not isinstance(tools, type([])):
        tools = [tools]
    gkey = _setup_global_tools(env)
    _global_tools[gkey].extend(tools)
    return env.Require(tools)
    

def _findToolFile(env, name):
    global _tool_matches
    # Need to know if the cache is enabled or not.
    esv._update_variables(env)
    cache = esv.ToolCacheVariables(env)
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
        _tool_matches = []
        for dirpath, dirnames, filenames in os.walk(env.Dir('#').get_abspath(),
                                                    followlinks=True):
            hidden = [d for d in dirnames if d.startswith('.')]
            for d in hidden:
                dirnames.remove(d)
            if 'site_scons' in dirnames:
                dirnames.remove('site_scons')
            if 'apidocs' in dirnames:
                dirnames.remove('apidocs')
            _tool_matches.extend([os.path.join(dirpath, file)
                                  for file in filenames if
                                  toolpattern.match(file)])
        # Update the cache
        cache.store(env, '_tool_matches', "\n".join(_tool_matches))
        print("Found %d tool files in source tree, cached in %s" %
              (len(_tool_matches), toolcache))

    toolFileName = "tool_" + name + ".py"
    return [f for f in _tool_matches if toolFileName == os.path.basename(f)]


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
        if name in global_exports:
            tool = global_exports[name]
        else:
            raise SCons.Errors.StopError("Tool error: " + 
                                         toolScript +
                                         " does not export symbol '" + name + "'")
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
_tool_dict = {}

def _Tool(env, tool, toolpath=None, **kw):
    env.LogDebug("eol_scons.Tool(%s,%s,kw=%s)" % (env.Dir('.'), tool, str(kw)))
    name = str(tool)
    env.LogDebug("...before applying tool %s: %s" % (name, esd.Watches(env)))

    if SCons.Util.is_String(tool):
        name = env.subst(tool)
        tool = None
        
        # Is the tool already in our tool dictionary?
        if name in _tool_dict:
            env.LogDebug("Found tool %s already loaded" % name)
            if not kw:
                tool = _tool_dict[name]
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
            _tool_dict[name] = tool

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
            toolpath = [env._find_toolpath_dir(tool) for tool in toolpath]
            tool = SCons.Tool.Tool(*(name, toolpath), **kw)
            env.LogDebug("Tool loaded: %s" % name)
            # If the tool is not specialized with keywords, then we can 
            # stash this particular instance and avoid reloading it.
            if tool and not kw:
                _tool_dict[name] = tool
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
    # SConstruct file.  However, it is left unused in favor of adding a
    # simple SetHelp() call at the end of SConstruct.
    #
    # env.SetHelp()
    #
    return tool


def _Require(env, tools):
    applied = []
    if not isinstance(tools, type([])):
        tools = [tools]
    env.LogDebug("eol_scons.Require[%s]" % ",".join([str(x) for x in tools]))
    for t in tools:
        try:
            tool = env.Tool(t)
            if tool:
                applied.append(tool)
        except SCons.Errors.EnvironmentError as ex:
            print("Error loading tool %s: %s" % (str(t), str(ex)))
            raise
    return applied


def generate(env, **kw):
    """
    Generate the basic eol_scons customizations for the given environment,
    including applying any eol_scons global tools.  Any default tool should
    have already been applied, or else this is being called by the
    eol_scons hook tool default.py.
    """
    Debug("Entering eol_scons.tool.generate()...")
    if hasattr(env, "_eol_scons_generated"):
        env.LogDebug("skipping _generate(), already applied")
        return
    env._eol_scons_generated = True

    # Add methods local to this module.
    env.AddMethod(_GlobalTools, "GlobalTools")
    env.AddMethod(_RequireGlobal, "RequireGlobal")
    env.AddMethod(_Tool, "Tool")
    env.AddMethod(_Require, "Require")

    # Add other methods
    eol_scons.methods._addMethods(env)
    eol_scons.variables._update_variables(env)

    name = env.Dir('.').get_path(env.Dir('#'))
    env.LogDebug("Generating eol defaults for Environment(%s) @ %s" % 
                 (name, env.Dir('#').get_abspath()))

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
    env.PrependUnique(CPPPATH=['#'])

    # Override the library builders to share targets across a project.
    eol_scons.library.ReplaceLibraryBuilders(env)

    # Pass on certain environment variables, especially those needed
    # for automatic checkouts.
    env.PassEnv(r'CVS.*|SSH_.*|GIT_.*')

    _apply_global_tools(env)
    return env


def export_qt_module_tool(modules):
    """
    The qt4 or qt5 tool must have been required first to specify the 
    Qt version for which this module should be added.  If not already
    specified, then qt4 is assumed.
    """
    kw = {}
    module = modules[0]
    dependencies = [m.lower() for m in modules[1:]]
    def qtmtool(env):
        # Make sure explicit Qt5 modules apply qt5 tool.
        env.LogDebug('in tool function for module %s' % (module))
        deps = dependencies[:]
        if module.startswith('Qt5'):
            env.Require(['qt5'])
        qtversion = env.get('QT_VERSION')
        if qtversion is None:
            env.Require(['qt4'])
        if qtversion == 5:
            # Qt5 modules have Qt5 as the prefix, so enforce that here.
            # Then look up dependencies again.
            if not module.startswith('Qt5') and module.startswith('Qt'):
                m5 = "Qt5" + module[2:]
                modules5 = [m for m in _qtmodules if m[0] == m5]
                if not modules5:
                    raise SCons.Errors.StopError("no Qt5 module " + m5)
                deps = [m.lower() for m in modules5[0][1:]]
        env.Require(deps)
        env.EnableQtModules([module])
    kw[module.lower()] = qtmtool
    SCons.Script.Export(**kw)

_qtmodules = [
    ('QtCore',),
    ('QtSvg', 'QtCore'),
    ('QtGui', 'QtCore'),
    ('QtNetwork', 'QtCore'),
    ('QtXml', 'QtCore'),
    ('QtXmlPatterns', 'QtXml'),
    ('QtSql',),
    ('QtOpenGL',),
    ('QtXml',),
    ('QtDesigner',),
    ('QtHelp',),
    ('QtTest',),
    ('QtWebKit',),
    ('QtDBus',),
    ('QtMultimedia',),
    ('QtScript',),
    ('QtScriptTools', 'QtScript'),
    ('QtUiTools', 'QtGui'),

    ('Qt5Core',),
    ('Qt5Gui', 'Qt5Core'),
    ('Qt5Svg', 'Qt5Core'),
    ('Qt5Widgets', 'Qt5Core'),
    ('QtWidgets', 'Qt5Core'),
    ('Qt5Network', 'Qt5Core'),
    ('Qt5Xml', 'Qt5Core'),
    ('Qt5PrintSupport', 'Qt5Core'),
    ('QtPrintSupport', 'Qt5Core'),
    ('Qt5XmlPatterns', 'Qt5Xml'),
    ('Qt5Sql',),
    ('Qt5OpenGL',),
    ('Qt5Xml',),
    ('Qt5Designer',),
    ('Qt5Help',),
    ('Qt5Test',),
    ('Qt5WebKitWidgets',),
    ('QtWebKitWidgets',),
    ('Qt5WebEngine',),
    ('QtWebEngine',),
    ('Qt5WebView', 'Qt5WebEngineWidgets'),
    ('QtWebView', 'Qt5WebEngineWidgets'),
    ('Qt5WebEngineWidgets',),
    ('QtWebEngineWidgets',),
    ('Qt5DBus',),
    ('Qt5Multimedia',),
    ('Qt5Script',),
    
]


def DefineQtTools():
    for qtmod in _qtmodules:
        export_qt_module_tool(qtmod)

