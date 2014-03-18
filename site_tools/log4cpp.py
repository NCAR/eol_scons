
import os
import string

def generate(env):
    env.Tool('doxygen')
    env.Append(LIBS=["log4cpp", "pthread"])
    # If you need to find log4cpp headers and libs in a non-standard
    # location, then make sure the prefixoptions tool is loaded and
    # OPT_PREFIX set accordingly.
    env.AppendUnique(CPPDEFINES=["LOG4CPP_FIX_ERROR_COLLISION", ])
    env.AppendDoxref("log4cpp:http://log4cpp.sourceforge.net/api/")

def exists(env):
    return True

