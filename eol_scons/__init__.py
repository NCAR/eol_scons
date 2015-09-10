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

Nothing else in this module should be called from outside the package.  In
particular, all the symbols starting with an underscore are meant to be
private.  See the README file for the documentation for this module.
"""

import os
import sys
import traceback

import SCons.Tool
import SCons.Defaults

# For backward compatibility, import symbols to be used
# without specifying 'eol_scons' module 
from eol_scons.debug import Debug
from eol_scons.variables import GlobalOptions   # replaced by GlobalVariables
from eol_scons.variables import GlobalVariables
from eol_scons.variables import PathToAbsolute

from eol_scons.tool import generate, exists

# print("__init__ __file__=%s" % __file__)
try:
    _eolsconsdir
    Debug("eol_scons previously initialized")

except NameError:
    # print("eol_scons __init__.py: %s" % __file__)

    # Create the DefaultEnvironment which is used for SCons.Script
    # functions that are called as plain functions, without an environment.
    # In SCons/Defaults.py this becomes a global which is
    # returned on all successive calls.
    SCons.Defaults.DefaultEnvironment()

    _eolsconsdir = os.path.abspath(os.path.dirname(__file__))

    # Add the tools dir to the tool path.
    tools_dir = os.path.normpath(os.path.join(_eolsconsdir, "tools"))
    print("Using site_tools: %s" % (tools_dir))
    SCons.Tool.DefaultToolpath.insert(0, tools_dir)
     
    Debug("eol_scons.__init__ loaded: %s." % (__file__))

