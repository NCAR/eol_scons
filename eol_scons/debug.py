# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

from SCons.Script import ARGUMENTS

debug = ARGUMENTS.get('eolsconsdebug', None)


def _Dump(env, key=None):
    'Dump a value of the given key or else the whole Environment.'
    if not key:
        return env.Dump()
    if key not in env:
        return ''
    return env.Dump(key)


def SetDebug(spec):
    """
    Set the debugging specifier to enable or disable printing of debug
    messages and watches for construction variables.
    """
    global debug
    debug = spec
    if LookupDebug('parseconfig'):
        import eol_scons.parseconfig as pc
        pc.set_debug(True)


def GetSubdir(env):
    subdir = str(env.Dir('.').get_path(env.Dir('#')))
    if subdir == '.':
        subdir = 'root'
    return subdir


def AddVariables(variables):
    variables.Add('eolsconsdebug',
"""
Enable debug messages from eol_scons.  Setting to 1 just enables
messages.  Or, set it to a comma-separated list of construction variables
to print before and after tools are applied.  Example:
  eolsconsdebug=LIBPATH,_LIBFLAGS,LIBS
Include a tool name to enable extra debugging in that tool, if it supports it, eg:
  eolsconsdebug=doxygen
""",
                  None)


# A list of tools which have extra debugging, so they should not be
# treated as variables to dump when in the debug key list.
_debug_tools = ['doxygen', 'parseconfig']


def Watches(env):
    """
    Generate a string containing the current values of all the watched
    variables, if any.
    """
    text = "no watches specified"
    if debug and debug != '1':
        variables = [v.strip() for v in debug.split(',')]
        values = ["%s=%s" % (v, _Dump(env, v))
                  for v in variables if v not in _debug_tools]
        if values:
            text = "\n  " + "\n  ".join(values)
    return text


def LookupDebug(tool):
    """
    Tools use this to see if their tool name appears in the debug key list,
    meaning the tool should print extra debugging messages.  Return true if
    the name exists in the list.  This function, unlike Watches(), does not
    check if the key is in the _debug_tools list, so it actually can be
    used to check if anything appears in the debug list.
    """
    return debug and (tool in [v.strip() for v in debug.split(',')])


def Debug(msg, env=None):
    """Print a debug message if the global debugging flag is true."""
    LogDebug(env, msg)


def LogDebug(env, msg):
    if debug:
        context = ""
        if env:
            context = GetSubdir(env) + ": "
        print("%s%s" % (context, msg))


SetDebug(debug)
