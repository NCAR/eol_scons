# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
"""
Override the built-in scons default tool.  This way Environments
created with the 'default' tool, which is virtually all of them, also
automatically get the eol_scons extensions applied.
"""

import SCons.Tool

import eol_scons.tool
from eol_scons.debug import Debug

_default_tool_list = None


def _apply_default_tool(env):
    """
    This is just an optimization which avoids searching the filesystem
    every time SCons needs to load all the default tools.  The original
    approach was the same as it is for other 'extended' tools like gcc:

    import SCons.Tool.default
    SCons.Tool.default.generate(env)

    The default tool just loads a list of platform-specific tool modules,
    so this function caches that list and the loaded tool modules.

    We only need to find the tools once, so
    subvert the SCons.Tool.default.generate(env) implementation with our
    own implementation here.  First time through, accumulate the default
    list of tool names, cache it for the next time around, and stash the
    list of instantiated default tools.  We can cache the names returned
    by tool_list in tools.cache, and then we can create the Tool()
    instances for those names and store them in a local variable for
    re-use on each new Environment.
    """

    # Install the default tools for the platform.  This used to cache the
    # tool names in the global variable cache, but that only had an effect
    # the first time through, since after that all the instantiated tools
    # would be in _default_tool_list.  Better to skip the cache and just
    # get them fresh on each startup, since the real optimization comes
    # from not needing to reload them for every Envioronment that gets
    # created.
    global _default_tool_list
    if _default_tool_list is None:
        toolnames = []
        if env['PLATFORM'] != 'win32':
            toolnames = SCons.Tool.tool_list(env['PLATFORM'], env)
        else:
            toolnames = ['mingw']
        # Now instantiate a Tool for each of the names.
        Debug("Applying default tools: %s" % (",".join(toolnames)))
        _default_tool_list = [SCons.Tool.Tool(t) for t in toolnames]

    # Now apply the default tools
    for tool in _default_tool_list:
        tool(env)


def generate(env):

    # Apply the built-in default tool before applying the eol_scons
    # customizations and tools.
    _apply_default_tool(env)

    # Pass off the rest of eol_scons initialization to the eol_scons.tool
    # module.
    eol_scons.tool.generate(env)

    # Note that we do not modify the tool path here.  This module is not
    # found by scons unless it is already on the tool path, meaning
    # eol_scons was already initialized by an import or something else.


def exists(env):
    return 1
