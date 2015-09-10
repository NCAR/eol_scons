# -*- python -*-
# Copyright 2007 UCAR, NCAR, All Rights Reserved
"""
"""

debug = False

def SetDebug(enable):
    """Set the flag to enable or disable printing of debug messages."""
    global debug
    debug = enable

def GetSubdir(env):
    subdir = str(env.Dir('.').get_path(env.Dir('#')))
    if subdir == '.':
        subdir = 'root'
    return subdir

def Debug(msg, env=None):
    """Print a debug message if the global debugging flag is true."""
    if debug:
        context = ""
        if env:
            context = GetSubdir(env) + ": "
        print("%s%s" % (context, msg))

