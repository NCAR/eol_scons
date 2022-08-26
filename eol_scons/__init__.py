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

from SCons.Script import EnsurePythonVersion

EnsurePythonVersion(3, 6)

# We are trying to migrate away from checking out eol_scons as the site_scons
# directory.  Instead eol_scons should be a subdirectory of site_scons.  So
# warn when this file is not being executed from the __init__.py in the parent
# directory.

_execmsg = """
*** Importing from site_scons/eol_scons has been deprecated.
*** The repository should be a subdirectory of site_scons named eol_scons.
"""

if bool("__eol_scons_init_exec__" not in globals() and
        __file__.endswith("site_scons/eol_scons/__init__.py")):
    print(_execmsg)

import os
import sys
from pathlib import Path

import SCons.Tool
import SCons.Defaults

# For backward compatibility, import symbols into the eol_scons package
# namespace.
from eol_scons.debug import Debug
from eol_scons.debug import LookupDebug
from eol_scons.variables import GlobalVariables
from eol_scons.variables import PathToAbsolute
from eol_scons.tool import DefineQtTools
from eol_scons.methods import EnableInstallAlias
from eol_scons.methods import PrintProgress


def _run_script(argname, name=None):
    if name is None:
        name = argname
    script = Path(__file__).parent.joinpath("../scripts").joinpath(name)
    script = script.resolve()
    args = [script] + sys.argv[sys.argv.index(argname)+1:]
    PrintProgress("Executing: %s" % (" ".join(map(str, args))))
    os.execv(script, args)


def RunScripts():
    """
    Use scons to provide a hook to scripts shared through eol_scons.  When a
    known script name is on the scons command-line, exec that script with all
    the succeeding arguments.  Note that the script cannot use single-hyphen
    arguments, because scons will catch those and act on them.  However, any
    double-hyphen arguments not recognized by scons will be ignored and passed
    to the script.
    """
    if 'build_rpm' in sys.argv:
        _run_script('build_rpm', 'build_rpm.sh')


# This would be needed if the eol_scons package were going to be loaded as
# a tool by installing it under a site_tools directory somewhere.  However,
# I don't think we're going to support that.  I think it's more flexible to
# just install as a package somewhere.  If it needs to be loaded like a
# tool without importing eol_scons explicitly, then the eol_scons.py tool
# module can be installed into site_tools somewhere.

# from eol_scons.tool import generate, exists

Debug("__init__ __file__=%s" % __file__)

PrintProgress("Loading eol_scons from %s..." %
              (os.path.abspath(os.path.dirname(__file__))))

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
