# -*- python -*-
# Copyright 2007 UCAR, NCAR, All Rights Reserved

from __future__ import print_function

import os
import re

import subprocess as sp

_debug = False

import SCons.Util

"""
Notes on PKG_CONFIG environment variables.

pkg-config searches PKG_CONFIG_PATH first, then PKG_CONFIG_LIBDIR,
or if that is not defined, the default system path, which can be
displayed by:
    pkg-config --variable pc_path pkg-config

To see which pkg-config file will be used for a module, in this case
netcdf, do:
    pkg-config --path netcdf

For a cross-build you may want to override PKG_CONFIG_LIBDIR and not
PKG_CONFIG_PATH, to ensure that pkg-config files for only the desired
architecture are found.

When pkg-config is run by this tool its environment is set from the
ENV member of the build Environment. (An overuse of the word!)
This tool does not propagate PKG_CONFIG_* variables from the Unix
environment, os.environ, to ENV. The user must set them:
    env = Environment(ENV={'PKG_CONFIG_LIBDIR': '/usr/lib/armel-linux-gnu/pkg-config'})
or
    env.PrependENVPath('PKG_CONFIG_PATH', '/path/to/custom/pcfiles')
"""

is_String = SCons.Util.is_String
is_List = SCons.Util.is_List

def _string_env(env):
    """
    This is taken from SCons.Action._subproc to convert non-string
    environment values to to strings.
    """
    new_env = {}
    for key, value in env.items():
        if is_List(value):
            # If the value is a list, then we assume it is a path list,
            # because that's a pretty common list-like value to stick
            # in an environment variable:
            value = SCons.Util.flatten_sequence(value)
            new_env[key] = os.pathsep.join([str(path) for path in value])
        else:
            # It's either a string or something else.  If it's a string,
            # we still want to call str() because it might be a *Unicode*
            # string, which makes subprocess.Popen() gag.  If it isn't a
            # string or a list, then we just coerce it to a string, which
            # is the proper way to handle Dir and File instances and will
            # produce something reasonable for just about everything else:
            new_env[key] = str(value)
    return new_env


def _extract_results(text):
    # The string result and integer returncode are coded in the cached
    # string as '<returncode>,<resultstring>'.  Sometimes the result
    # strings have more than one line, so we must be careful to extract the
    # rest of the string, including any newlines.
    m = re.match(r"^([-+]?\d+),", text)
    if m:
        return (int(m.group(1)), text[m.end():])
    else:
        return (-1, text)


def getConfigCache(env):
    cache = env.get("_config_cache")
    if cache is None:
        cache = {}
        env["_config_cache"] = cache
    return cache


def _get_config(env, search_paths, config_script, args):
    """
    Return a (returncode, output) tuple for a call to @p config_script.

    By collecting both the return code and the output result from the same
    call to the config script, it is not necessary to first call the config
    script just to test whether the package's config script is installed.
    If there is a non-zero return code from the config script command, then
    tools can continue with other methods of configuring the tool.

    The config results are cached in the calling Environment, so the
    command does not need to be run every time a tool needs to run the same
    config script.  However, the results are specific to the Environment,
    since the results can change depending upon the Environment running
    them.  For example, PKG_CONFIG_PATH or PKG_CONFIG_LIBDIR might be different
    for different environments, and cross-build environments will return different
    results.  The goal is to avoid redundant runs of the same config script
    when called for the same environment, such as redundant applications of
    the same tool.
    """
    result = None
    if _debug: print("_get_config(%s,%s): " % (config_script, ",".join(args)))
    # See if the output for this config script call has already been cached.
    name = re.sub(r'[^\w]', '_', config_script + " ".join(args))
    cache = getConfigCache(env)
    result = cache.get(name)
    if result:
        if _debug: print("  cached: %s" % (result))
        return _extract_results(result)
    if not result:
        if search_paths:
            search_paths = [ p for p in search_paths if os.path.exists(p) ]
            env.LogDebug("Checking for %s in %s" % 
                         (config_script, ",".join(search_paths)))
            config = env.WhereIs(config_script, search_paths)
        else:
            config = config_script
        env.LogDebug("Found: %s" % config)
    if not result and config:
        # The env dictionary must be converted to strings or else
        # execve() complains.
        psenv = _string_env(env['ENV'])
        if False:
            # This is not done by default because it violates the scons
            # principle of precisely controlling the build environment.
            PassPkgConfigPath(env, psenv)
        if _debug:
            print("calling Popen([%s])" % ",".join([config]+args))
            print("\n".join(["%s=%s" % (k,v) for k,v in psenv.items()]))
        try:
            child = sp.Popen([config] + args, stdout=sp.PIPE, env=psenv)
            result = child.communicate()[0]
            result = result.decode().strip()
            # Ubuntu 16.04 on Vortex had a mal configured cpp_common.pc libs entry.
            # e.g. -l:/usr/lib/libcpp_common.so - clean it up here.
            result = result.replace('-l:/','/')
            cache[name] = "%s,%s" % (child.returncode, result)
            result = (child.returncode, result)
        except OSError:
            # If the config script cannot be found, then the package must
            # not exist either.
            result = (1, None)
    if not result:
        result = (-1, "")
    if _debug: print("   command: %s" % (str(result)))
    return result


def PassPkgConfigPath(env, psenv=None):
    """
    Propagate PKG_CONFIG_PATH and PKG_CONFIG_LIBDIR to the scons process
    environment (ENV) if they are set anywhere in the scons construction or
    process environment.
    This is not done by default because it violates the scons principle of
    precisely controlling the build environment.  If a build did not
    explicitly pass PKG_CONFIG_PATH or PKG_CONFIG_LIBDIR into ENV, then it
    may have a good reason for that.

    """
    if psenv is None:
        psenv = env['ENV']
    for pcp in ('PKG_CONFIG_PATH', 'PKG_CONFIG_LIBDIR'):
        if pcp in psenv:
            pass
        elif pcp in os.environ:
            psenv[pcp] = os.environ.get(pcp)

def RunConfig(env, command):
    """
    Run the config script command and return tuple (returncode, output).
    """
    args = command.split()
    config_script = args[0]
    args = args[1:]
    return _get_config(env, None, config_script, args)[1]


def CheckConfig(env, command):
    """
    Return True if the pkg-config-like command succeeds (returns 0).

    The output is cached in the environment, so subsequent requests for the
    same config command will not need to execute the command again.
    """
    args = command.split()
    config_script = args[0]
    args = args[1:]
    return _get_config(env, None, config_script, args)[0] == 0


def ParseConfig(env, command, function=None, unique=True):
    """
    Like Environment.ParseConfig, except do not raise OSError if the
    command fails, and the config script results are cached in the
    Environment.  If the command succeeds, then merge the results flags
    into the Environment and return True.  Otherwise return False.
    """
    args = command.split()
    result = _get_config(env, None, args[0], args[1:])
    if result[0] == 0:
        if not function:
            env.MergeFlags(result[1], unique)
        else:
            function(result[1], unique)
        return True
    return False


def _filter_ldflags(flags):
    "Fix ldflags from config scripts which return standard library dirs."
    fields = flags.split()
    fields = [ f for f in fields if not re.match(r'^-L/usr/lib(64)?$', f) ]
    flags = " ".join(fields)
    return flags


def PkgConfigPrefix(env, pkg_name, default_prefix = "$OPT_PREFIX"):
    """Search for a config script and parse the output."""
    search_prefixes = ['/usr', '/usr/local','/opt/homebrew','/mingw64']
    search_paths = [ os.path.join(env.subst(x),"bin")
                     for x in [y for y in search_prefixes if y] ]
    prefix = None
    prefix = _get_config(env, search_paths, 'pkg-config',
                             ["--variable=prefix", pkg_name])[1]
    if not prefix:
        prefix = default_prefix
    return prefix

def PkgConfigVariable(env, pkg_name, variable):
    """Search for a config script and parse the output."""
    search_prefixes = ['/usr', '/usr/local','/opt/homebrew','/mingw64']
    search_paths = [ os.path.join(env.subst(x),"bin")
                     for x in [y for y in search_prefixes if y] ]
    prefix = None
    var = '--variable=' + variable
    output = _get_config(env, search_paths, 'pkg-config',
                             [var, pkg_name])[1]
    return output


