# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
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

import sys
import traceback

import SCons.Variables
import SCons.Script
from SCons.Script import Variables
from SCons.Script import DefaultEnvironment
from SCons.Script import BoolVariable

import eol_scons.debug
from eol_scons.methods import PrintProgress

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
        eol_scons.debug.AddVariables(_global_variables)
        _global_variables.AddVariables(
            BoolVariable('eolsconscache',
                         'Enable tools.cache optimization.',
                         _enable_cache))
        PrintProgress("Config files: %s" % (_global_variables.files))
    return _global_variables

class VariableCache(SCons.Variables.Variables):
    """
    Add a file-backed cache store to Variables, originally to be used to
    cache locations of tool files embedded in the source tree and to cache
    output from expensive config scripts across builds.  The file store is
    disabled by default now, since it can cause confusion when tool files
    change in the tree but are not discovered because of the cache.  Also,
    the results of config scripts will change depending upon the
    environment running them.  For example, PKG_CONFIG_PATH might be
    different for different environments, and cross-build environments will
    return different results.  Therefore this cache is no longer used for
    config script results, and it is only used for tool file locations if
    explicitly enabled.
    """
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
        if key in env:
            value = env[key]
            env.LogDebug("returning %s cached value: %s" % (key, value))
        else:
            env.LogDebug("no value cached for %s" % (key))
        return value

    def store(self, env, name, value):
        # Update the cache
        key = self.cacheKey(name)
        env[key] = value
        if self.getPath():
            self.Save(self.getPath(), env)
        env.LogDebug("Updated %s to value: %s" % (key, value))


def ToolCacheVariables(env):
    global _cache_variables
    if not _cache_variables:
        env.LogDebug(
            "creating _cache_variables: eolsconsdebug=%s, eolsconscache=%s" %
            (eol_scons.debug.debug, _enable_cache))
        cfile = "#/tools.cache"
        cfile = env.File(cfile).get_abspath()
        if _enable_cache:
            _cache_variables = VariableCache(cfile)
            print("Tool settings cache: %s" % (_cache_variables.getPath()))
        else:
            _cache_variables = VariableCache(None)
            env.LogDebug("Tool cache is disabled by default. "
                         "Enable it by setting eolsconscache=1.")
    return _cache_variables


def PathToAbsolute(path, env):
    "Convert a Path variable to an absolute path relative to top directory."
    apath = env.Dir('#').Dir(path).get_abspath()
    # print("Converting PREFIX=%s to %s" % (path, apath))
    return apath


def _GlobalVariables(env, cfile=None):
    return GlobalVariables(cfile, env)


def _CacheVariables(env):
    return ToolCacheVariables(env)


def _AliasHelpText(env):
    """
    Generate help text for all the aliases by tapping into the default
    AliasNameSpace, and listing their dependency nodes.
    """
    aliases = SCons.Node.Alias.default_ans
    # Get the alias keys (names) as a list
    names = list(aliases)
    names.sort()
    text = "Aliases:\n"
    width = max([len(n) for n in [""] + names])
    for name in names:
        node = aliases[name]
        row = " "*(1 + width-len(name))
        row += "%s: %s" % (name, ", ".join([str(n) for n in
                                            node.all_children()]))
        if len(row) > 75:
            row = row[:75] + '...'
        text += row
        text += "\n"
    return text


def _GenerateHelpText(env):
    """
    Generate the eol_scons default help text, which includes the help text
    from all the global variables, a list of aliases, and also a list of
    the default targets if the --list-defaults option is set.
    """
    variables = env.GlobalVariables()
    variables.Update(env)
    text = variables.GenerateHelpText(env)

    try:
        # In case this has been done before, ignore any exceptions.
        SCons.Script.AddOption("--list-aliases", dest="listaliases",
                               action="store_true")
    except Exception as ex:
        env.LogDebug(str(ex))

    text += "\n"
    if env.GetOption("listaliases"):
        text += _AliasHelpText(env)
    else:
        text += "Aliases can be listed with '-h --list-aliases'.\n"

    try:
        SCons.Script.AddOption("--list-defaults", dest="listdefaults",
                               action="store_true")
    except Exception as ex:
        env.LogDebug(str(ex))

    if env.GetOption("listdefaults"):
        dtargets = list(set([str(n) for n in SCons.Script.DEFAULT_TARGETS]))
        dtargets.sort()
        text += "\nDefault targets:\n"
        for target in dtargets:
            text += "  %s\n" % (str(target))
    else:
        text += "Default targets can be included with '-h --list-defaults'.\n"

    try:
        SCons.Script.AddOption("--list-installs", dest="listinstalls",
                               action="store_true")
    except Exception as ex:
        env.LogDebug(str(ex))

    if env.GetOption("listinstalls"):
        text += "\nInstall targets:\n"
        for target in env.FindInstalledFiles():
            text += "  %s\n" % (str(target))
    else:
        text += "Install targets can be listed with '-h --list-installs'.\n"

    return text


def _SetHelp(env, text=None):
    """
    Override the SConsEnvironment Help method to first erase any previous
    help text.  This can help if multiple SConstruct files in a project
    each try to generate the help text all at once.  If @p text is None,
    then generate the help text from the global variables.  To clear the
    help text to an empty string, pass "" in @p text.

    Note that scons help is somewhat convoluted.  Before v3, HelpFunction()
    always appended to the current help text.  Since v3, it resets the help
    text by default, unless the append keyword is True, but the append
    keyword does not exist before v3.  So to try to be consistent, this
    method always resets the help text first.  The AddHelp() method is
    provided to explicitly append to the help text.

    Therefore, to generate and install all the default help text, and then
    append any custom text, use this code:

        env.SetHelp()
        env.AddHelp("See here for custom help.")

    To set the custom help first, then append the generated help text, use
    this:

        env.SetHelp("See here for custom help.")
        env.AddHelp()
    """
    SCons.Script.help_text = None
    if text is None:
        text = _GenerateHelpText(env)

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


def _AddHelp(env, text=None):
    """
    Append help text to the current help text.  If text is None, generate
    the default text and append it.  See SetHelp().
    """
    if text is None:
        text = _GenerateHelpText(env)

    # Because of the change in how HelpFunction() works between v2.3 and
    # v3.0, the only way to be sure we always append to the current
    # help_text is to manipulate help_text directly.
    SCons.Script.help_text = SCons.Script.help_text + text


def _update_variables(env):

    # Add our variables methods to this Environment.
    env.AddMethod(_GlobalVariables, "GlobalVariables")
    env.AddMethod(_CacheVariables, "CacheVariables")
    # Alias for temporary backwards compatibility
    env.AddMethod(_GlobalVariables, "GlobalOptions")

    # So that only the last Help text setting takes effect, rather than
    # duplicating info when SConstruct files are loaded from sub-projects.
    env.AddMethod(_SetHelp, "SetHelp")
    env.AddMethod(_AddHelp, "AddHelp")
    env.AddMethod(_AliasHelpText, "AliasHelpText")
    env.AddMethod(_GenerateHelpText, "GenerateHelpText")

    # Do not update the environment with global variables unless some
    # global variables have been created.
    if _global_variables and _global_variables.keys():
        _global_variables.Update(env)

    if 'eolsconsdebug' in env:
        eol_scons.debug.SetDebug(env['eolsconsdebug'])
    if 'eolsconscache' in env:
        global _enable_cache
        _enable_cache = env['eolsconscache']
