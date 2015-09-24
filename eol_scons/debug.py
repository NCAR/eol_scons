# -*- python -*-
# Copyright 2007 UCAR, NCAR, All Rights Reserved
"""
"""

debug = None

def _Dump(env, key=None):
    'Dump a value of the given key or else the whole Environment.'
    if not key:
        return env.Dump()
    if not env.has_key(key):
        return ''
    return env.Dump(key)

def SetDebug(spec):
    """
    Set the debugging specifier to enable or disable printing of debug
    messages and watches for construction variables.
    """
    global debug
    debug = spec

def GetSubdir(env):
    subdir = str(env.Dir('.').get_path(env.Dir('#')))
    if subdir == '.':
        subdir = 'root'
    return subdir

def AddVariables(variables):
    # This is not really a path, but ListVariable and EnumVariable seem to
    # require that you know what will be listed ahead of time.  There is no
    # plain string variable.
    variables.Add('eolsconsdebug',
"""Enable debug messages from eol_scons.  Setting to 1 just enables
messages.  Or, set it to a comma-separated list of construction variables
to print before and after tools are applied.  Example:
eolsconsdebug=LIBPATH,_LIBFLAGS,LIBS""",
                  None)

def Watches(env):
    """
    Generate a string containing the current values of all the watched
    variables, if any.
    """
    if debug and debug != '1':
        variables = [v.strip() for v in debug.split(',')]
        return "\n  " + "\n  ".join(["%s=%s" % (v, _Dump(env, v))
                                     for v in variables])
    return "no watches specified"

def Debug(msg, env=None):
    """Print a debug message if the global debugging flag is true."""
    if debug:
        context = ""
        if env:
            context = GetSubdir(env) + ": "
        print("%s%s" % (context, msg))

