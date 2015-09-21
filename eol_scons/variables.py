# -*- python -*-
# Copyright 2007 UCAR, NCAR, All Rights Reserved

"""Enhanced support for Scons Variables.

It used to be that the default config file was hardcoded to be in the
parent directory of this site_scons tree, but that fails when site_scons
is imported by a SConstruct file from a different relative path.  So now
this function implicitly creates an environment if one is not passed in,
so the cfile path can be resolved with the usual SCons notation, which by
default is the directory containing the SConstruct file.  The creation of
the default environment is not recursive because this function is not
called (via _update_variables) until global Variables have been added.
"""

import os
import sys

import SCons.Variables
from SCons.Script import Variables
from SCons.Script import DefaultEnvironment
from SCons.Script import BoolVariable

import debug
import traceback

_global_variables = None
_cache_variables = None
_default_cfile = "#/config.py"
_enable_cache = False

def GlobalVariables(cfile=None, env=None):
    """Return the eol_scons global variables."""
    global _global_variables
    if not _global_variables:
        if not env:
            env = DefaultEnvironment()
        if not cfile:
            cfile = _default_cfile
        cfile = env.File(cfile).get_abspath()
        _global_variables = Variables(cfile)
        _global_variables.AddVariables(
            BoolVariable('eolsconsdebug',
                         'Enable debug messages from eol_scons.',
                         debug.debug))
        _global_variables.AddVariables(
            BoolVariable('eolsconscache',
                         'Enable tools.cache optimization.',
                         _enable_cache))
        print("Config files: %s" % (_global_variables.files))
    return _global_variables

def GlobalOptions(cfile=None, env=None):
    """
    GlobalOptions() has been replaced by GlobalVariables(). Generate an error
    if it's called.
    """
    # Print the stack up to the call to this function
    stack = traceback.extract_stack()
    print >> sys.stderr, '\n'.join(traceback.format_list(stack[:-1]))
    # Raise a StopError
    errmsg = "eol_scons.GlobalOptions() is no longer supported; " \
             "use eol_scons.GlobalVariables() instead"
    raise SCons.Errors.StopError, errmsg                       

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
            debug.Debug("returning %s cached value: %s" % (key, value), env)
        else:
            debug.Debug("no value cached for %s" % (key), env)
        return value
        
    def store(self, env, name, value):
        # Update the cache
        key = self.cacheKey(name)
        env[key] = value
        if self.getPath():
            self.Save(self.getPath(), env)
        debug.Debug("Updated %s to value: %s" % (key, value), env)


def ToolCacheVariables(env):
    global _cache_variables
    if not _cache_variables:
        debug.Debug("creating _cache_variables: eolsconsdebug=%s, eolsconscache=%s" %
              (debug.debug, _enable_cache))
        cfile = "#/tools.cache"
        cfile = env.File(cfile).get_abspath()
        if _enable_cache:
            _cache_variables = VariableCache(cfile)
            print("Tool settings cache: %s" % (_cache_variables.getPath()))
        else:
            _cache_variables = VariableCache(None)
            print("Tool cache will not be used. "
                  "(It is now disabled by default.) "
                  "It can be enabled by setting eolsconscache=1")
    return _cache_variables


def PathToAbsolute(path, env):
    "Convert a Path variable to an absolute path relative to top directory."
    apath = env.Dir('#').Dir(path).get_abspath()
    # print("Converting PREFIX=%s to %s" % (path, apath))
    return apath

def _update_variables(env):
    # Do not update the environment with global variables unless some
    # global variables have been created.
    if _global_variables and _global_variables.keys():
        _global_variables.Update(env)

    if env.has_key('eolsconsdebug'):
        debug.debug = env['eolsconsdebug']
    if env.has_key('eolsconscache'):
        global _enable_cache
        _enable_cache = env['eolsconscache']

