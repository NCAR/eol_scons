# -*- python -*-
# Copyright 2007 UCAR, NCAR, All Rights Reserved

"""
Tool methods invoked when tools/eol_scons.py or hooks/default.py are
loaded as a tool.  This module is not actually a scons tool, it is just the
functionality which applies the eol_scons extensions as if it were a tool.
"""

import SCons.Tool

from eol_scons import Debug

import eol_scons.methods as esm
import eol_scons.variables as esv
import eol_scons.library

_global_tools = {}

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
    gkey = env.Dir('.').get_abspath()
    env['GLOBAL_TOOLS_KEY'] = gkey
    if not _global_tools.has_key(gkey):
        _global_tools[gkey] = []

    if env.has_key('GLOBAL_TOOLS'):
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


def generate(env, **kw):
    """
    Generate the basic eol_scons customizations for the given environment,
    including applying any eol_scons global tools.  Any default tool should
    have already been applied, or else this is being called by the
    eol_scons hook tool default.py.
    """
    if hasattr(env, "_eol_scons_generated"):
        env.LogDebug("skipping _generate(), already applied")
        return
    env._eol_scons_generated = True

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
                    raise SCons.Errors.StopError, "no Qt5 module "+m5
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
    ('Qt5Svg', 'Qt5Core'),
    ('Qt5Widgets', 'Qt5Core'),
    ('QtWidgets', 'Qt5Core'),
    ('Qt5Network', 'Qt5Core'),
    ('Qt5Xml', 'Qt5Core'),
    ('Qt5XmlPatterns', 'Qt5Xml'),
    ('Qt5Sql',),
    ('Qt5OpenGL',),
    ('Qt5Xml',),
    ('Qt5Designer',),
    ('Qt5Help',),
    ('Qt5Test',),
    ('Qt5WebKitWidgets',),
    ('QtWebKitWidgets',),
    ('Qt5DBus',),
    ('Qt5Multimedia',),
    ('Qt5Script',),
    
]


def DefineQtTools():
    for qtmod in _qtmodules:
        export_qt_module_tool(qtmod)

