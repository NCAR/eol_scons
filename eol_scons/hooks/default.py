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

from pathlib import Path
from eol_scons.methods import PrintProgress


# When the eol_scons package is imported, __init__.py sets up the tool path so
# this default tool is found first, besides doing other setup like adding all
# the other eol_scons tools to the tool path and creating the global default
# Environment.  Unfortunately this setup happens even when eol_scons is not
# being used in a SCons run, such as to import gitinfo or other modules. Maybe
# it's possible for __init__.py to only setup the tool path, and leave the
# rest of the eol_scons setup to happen when this tool is applied.  Or maybe
# it's about time there were a better way to share functionality like gitinfo
# outside of eol_scons...
#
# Anyway, this message was moved here from __init__.py so it would only be
# printed when scons is running and loading eol_scons tools.  It will no
# longer be printed when python code imports eol_scons for other modules.
#
# Give the top of the eol_scons package directory as the location.
PrintProgress("Loading eol_scons from %s..." %
              (Path(__file__).parent.parent.parent.resolve()))


# Once initialized, this will be a list[SCons.Tool.Tool]
_default_tool_list = None


def _load_default_tool_list(env):
    """
    This is just an optimization which avoids searching the filesystem
    every time SCons needs to load all the default tools.  The original
    approach was the same as it is for other 'extended' tools like gcc:

    import SCons.Tool.default
    SCons.Tool.default.generate(env)

    The default tool just loads a list of platform-specific tool modules, so
    this function loads the tools and also caches the list of instances. This
    caching assumes the PLATFORM and the corresponding default tool list will
    be the same for every Environment created.
    """
    global _default_tool_list
    if _default_tool_list is None:
        tools = []
        if env['PLATFORM'] != 'win32':
            tools = SCons.Tool.tool_list(env['PLATFORM'], env)
        else:
            tools = ['mingw']
        # Now instantiate a Tool for any tool names in the list.  As of SCons
        # 4.11, most of these will already be Tool instances, but prior to
        # that they were names.  Tool(t) when t is already a Tool just returns
        # t, so this works for all versions.
        _default_tool_list = [SCons.Tool.Tool(t) for t in tools]
    return _default_tool_list


def _apply_default_tool(env):
    tools = _load_default_tool_list(env)
    Debug("Applying default tools: %s" % (",".join(str(t) for t in tools)))
    # Now apply the default tools
    for tool in tools:
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
