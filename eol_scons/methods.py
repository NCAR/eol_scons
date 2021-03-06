# -*- python -*-
# Copyright 2007 UCAR, NCAR, All Rights Reserved

from __future__ import print_function

import os, re, glob

import SCons.Util
from SCons.Util import NodeList
from SCons.Script import DefaultEnvironment

import eol_scons.debug as esd
import eol_scons.chdir as chdir

_global_targets = {}

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
    if name not in _global_targets:
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
    if "LOCAL_TARGETS" not in env:
        env["LOCAL_TARGETS"] = {}
    local_tgts = env["LOCAL_TARGETS"]
    if name not in local_tgts:
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
    options = env.GlobalVariables()
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


# Include this as a standard part of Environment, so that other tools can
# conveniently add their doxref without requiring the doxygen tool.
def _AppendDoxref(env, ref):
    """
    Append to the DOXREF variable and force it to be a list.

    The DOXREF variable is a list of strings which are external doxygen
    references, in the form <tagfile>:<ref>.  Since tag files do not
    usually exist for external dependencies, those tools by convention add
    a construction variable as a DOXREF, like $LOG4CPP_DOXREF.  Then
    projects can supply explicit tagfiles with their references as they see
    fit.  The <ref> can be a url to online HTML documentation generated by
    doxygen, or it can be the path to HTML documentation on the local
    filesystem.  Empty DOXREF elements will be ignored by the doxygen tool.
    """
    # If the reference is a Doxygen target node, convert it into a
    # directory reference by stripping the html/index.html from it.
    if type(ref) != type(""):
        ref = ref.Dir('..').name
    if 'DOXREF' not in env:
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
    env.AddMethod(_AppendDoxref, "AppendDoxref")

    # For backwards compatibility:
    env.AddMethod(_Create, "Create")

