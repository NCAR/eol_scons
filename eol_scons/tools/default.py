
"""default

Override the built-in scons default tool and propagate the tool path,
so that we can extend the built-in tools even when they are not
specified explicitly in the tools list.
"""

import SCons.Tool

import eol_scons.tool
import eol_scons.methods
import eol_scons.variables

_default_tool_list = None

def generate(env):

    # CacheVariables is used here, so add the eol_scons methods
    eol_scons.methods._addMethods(env)

    # Update the environment with any global variables
    eol_scons.variables._update_variables(env)

    # Install the default tools for the platform.
    global _default_tool_list
    if _default_tool_list == None:

        # See if the default list of tool names is already in the cache
        cache = env.CacheVariables()
        key = "_eol_scons_default_tool_names"
        toolnames = cache.lookup(env, key)
        if not toolnames:
            if env['PLATFORM'] != 'win32':
                toolnames = SCons.Tool.tool_list(env['PLATFORM'], env)
            else:
                toolnames = ['mingw']
            cache.store(env, key, "\n".join(toolnames))
        else:
            toolnames = toolnames.split("\n")

        # Now instantiate a Tool for each of the names.
        _default_tool_list = [ SCons.Tool.Tool(t) for t in toolnames ]

    # Now apply the default tools
    for tool in _default_tool_list:
        tool(env)

    # Now do the rest of the eol_scons tool initialization
    eol_scons.tool.generate(env)

def exists(env):
    return 1
