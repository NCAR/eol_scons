# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
"""
Tool methods invoked when eol_scons extensions are loaded as a tool.
This tool module can be installed into a site_tools directory on the scons
search path to load eol_scons without explicitly importing it.  However,
since the eol_scons must still be imported, the eol_scons package must be
installed on the python system path or under a site_scons directory.

Loading eol_scons through this tool implies that the override of the
default tool is not wanted, so that hook is removed explicitly by this
tool.  Do not use this tool if eol_scons should be applied to all
Environments implicitly when they load the default tool.

The tool is named eol_scons_tool to distinguish it from the eol_scons
package.  Naturally if this tool were imported with the name eol_scons, it
would not then be possible to import the eol_scons package.
"""

import eol_scons
import eol_scons.tool

# This must be called right after importing and not in the generate()
# function.  We do not want to risk interfering with the load of the real
# default tool.
eol_scons.RemoveDefaultHook()


def exists(env):
    return 1


def generate(env, **kw):
    """
    Apply the eol_scons extensions to the given environment.
    """
    print("eol_scons tool generate()")
    eol_scons.tool.generate(env, **kw)
