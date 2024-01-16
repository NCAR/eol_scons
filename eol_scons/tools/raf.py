# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

# This tool works for source trees which do not contain the raf library
# source but still need to link to it.  If the raf source is in the source
# tree, then tool_raf.py tool will be loaded instead of this one.

# This tool expects that CPPPATH and LIBPATH have already been set
# appropriately using tools like prefixoptions or jlocal.

def generate(env):
    env.AppendLibrary('raf')


def exists(env):
    return True
