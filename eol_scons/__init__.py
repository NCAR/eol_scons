# -*- python -*-
# Copyright 2007 UCAR, NCAR, All Rights Reserved

"""
The eol_scons package for EOL extensions to standard SCons.

This package extends SCons in three ways: it overrides or adds methods for
the SCons Environment class.  See the methods.py module to see
the full list.

Second, this package adds the eol_scons/tools directory to the SCons tool path.
Most of the tools for configuring and building against third-party software
packages.

Lastly, this module itself provides an interface of a few functions, for
configuring and controlling the eol_scons framework outside of the
Environment methods.  These are the public functions:

GlobalVariables(): Returns the global set of variables (formerly known as
options) available in this source tree.

SetDebug(enable): set the global debugging flag to 'enable'.

Debug(msg): Print a debug message if the global debugging flag is true.

LookupDebug(tool): Some tools use this to see if their tool name appears in
the debug key list, meaning the tool should print extra debugging messages.

Nothing else in this module should be called from outside the package.  In
particular, all the symbols starting with an underscore are meant to be
private.  See the README file for the documentation for this module.
"""
from __future__ import print_function

import os
import sys
import traceback

import SCons.Tool
import SCons.Defaults

# For backward compatibility, import symbols into the eol_scons package
# namespace.
from eol_scons.debug import Debug
from eol_scons.debug import LookupDebug
from eol_scons.variables import GlobalOptions   # replaced by GlobalVariables
from eol_scons.variables import GlobalVariables
from eol_scons.variables import PathToAbsolute
from eol_scons.tool import DefineQtTools

# This would be needed if the eol_scons package were going to be loaded as
# a tool by installing it under a site_tools directory somewhere.  However,
# I don't think we're going to support that.  I think it's more flexible to
# just install as a package somewhere.  If it needs to be loaded like a
# tool without importing eol_scons explicitly, then the eol_scons.py tool
# module can be installed into site_tools somewhere.

# from eol_scons.tool import generate, exists

Debug("__init__ __file__=%s" % __file__)


def InstallToolsPath():
    "Add the eol_scons/tools dir to the tool path."
    Debug("Using site_tools: %s" % (tools_dir))
    SCons.Tool.DefaultToolpath.insert(0, tools_dir)
     
def InstallDefaultHook():
    "Add the hooks dir to the tool path to override the default tool."
    SCons.Tool.DefaultToolpath.insert(0, hooks_dir)

def RemoveDefaultHook():
    """
    Remove the path to the default override, for cases where eol_scons will
    be applied to Environments explicitly using the eol_scons.py tool
    module.
    """
    if hooks_dir in SCons.Tool.DefaultToolpath:
        SCons.Tool.DefaultToolpath.remove(hooks_dir)


# I'm not sure this could ever be run twice if it is only imported as a
# python package, since python should never import a package twice.  So
# maybe this extra machinery can be removed someday.

try:
    _eolsconsdir
    Debug("eol_scons previously initialized")

except NameError:
    _eolsconsdir = os.path.abspath(os.path.dirname(__file__))
    tools_dir = os.path.normpath(os.path.join(_eolsconsdir, "tools"))
    hooks_dir = os.path.normpath(os.path.join(_eolsconsdir, "hooks"))

    InstallToolsPath()
    DefineQtTools()

    # Create the DefaultEnvironment which is used for SCons.Script
    # functions that are called as plain functions, without an environment.
    # In SCons/Defaults.py this becomes a global which is returned on all
    # successive calls.  Also, create this here before the default.py hook
    # tool is added to the tool path, since that can cause infinite
    # recursion.
    Debug("Creating DefaultEnvironment()...")
    SCons.Defaults.DefaultEnvironment()
    InstallDefaultHook()
    Debug("eol_scons.__init__ loaded: %s." % (__file__))

