# -*- python -*-
# Copyright 2007 UCAR, NCAR, All Rights Reserved

"""Tool methods invoked when tools/eol_scons.py or tools/default.py are
loaded as a tool.
"""

import SCons.Tool

from eol_scons import Debug

import methods, variables, library

_global_tools = {}

def exists(env):
    return 1

def generate(env, **kw):
    """Generate the basic eol_scons customizations for the given
    environment, especially applying the scons built-in default tool
    and the eol_scons global tools."""

    if hasattr(env, "_eol_scons_generated"):
        Debug("skipping _generate(), already applied")
        return
    env._eol_scons_generated = True

    methods._addMethods(env)

    variables._update_variables(env)

    name = env.Dir('.').get_path(env.Dir('#'))
    Debug("Generating eol defaults for Environment(%s) @ %s" % 
          (name, env.Dir('#').get_abspath()), env)

    # Apply the built-in default tool before applying the eol_scons
    # customizations and tools.  We only need to find the tools once, so
    # subvert the SCons.Tool.default.generate(env) implementation with our
    # own implementation here.  First time through, accumulate the default
    # list of tool names, cache it for the next time around, and stash the
    # list of instantiated default tools.  We can cache the names returned
    # by tool_list in tools.cache, and then we can create the Tool()
    # instances for those names and store them in a local variable for
    # re-use on each new Environment.


    # Internal includes need to be setup *before* OptPrefixSetup or any
    # other includes, so that scons will scan for headers locally first.
    # Otherwise it looks in the opt prefix include first, and it notices
    # that the logx headers get installed there (even though not by
    # default).  This creates a dependency on the headers in that location,
    # which causes them to be installed even when the target is not
    # specifically 'install'.  The include arguments *are* (or used to be
    # and may someday again) re-ordered later on the command-line, putting
    # local includes first, but apparently that is not soon enough to
    # affect the scons scan.
    env.PrependUnique(CPPPATH=['#'])

    # The customized Library wrapper methods might be added directly to
    # envclass, as in _addMethods, except SCons overrides the instance
    # methods associated with builders, so I don't think that would work.
    # It should work to "chain" MethodWrapper, by calling AddMethod() to
    # add a function object which then calls the original MethodWrapper
    # instance.  However, this runs into problems with Environment.Clone().
    # When the Environment Builders are cloned, they are added back to the
    # BUILDERS dictionary, and that dictionary is especially designed to
    # update the Environment instance methods corresponding to the
    # Builders.  Maybe that's as it should be, but the point is that we
    # need to replace the standard builder with our own copy of the
    # builder.
    #
    # Can the global list of targets be acquired other than by intercepting
    # Library() just to register the global targets?  Perhaps when
    # GetGlobalTarget is called, it can search the SCons Node tree for a
    # target which matches that name?  That would be supremely simpler, as
    # long as the tree search is not too slow.  One problem may be
    # selecting among multiple nodes with similar names.  Which is the one
    # to which the wrapped Library call would have pointed?

    # Debug("Before wrapping Library: %s" % (_library_builder_str(env)))

    Debug("Replacing standard library builders with subclass", env)
    builder = SCons.Tool.createStaticLibBuilder(env)
    builder = library._LibraryBuilder(builder)
    env['BUILDERS']['StaticLibrary'] = builder
    env['BUILDERS']['Library'] = builder
    builder = SCons.Tool.createSharedLibBuilder(env)
    builder = library._LibraryBuilder(builder)
    env['BUILDERS']['SharedLibrary'] = builder

    # Debug("After wrapping Library: %s" % (_library_builder_str(env)))

    # if eolenv._creating_default_environment:
    #     Debug("Limiting DefaultEnvironment to standard scons tools.", env)
    #     return env

    # Pass on certain environment variables, especially those needed
    # for automatic checkouts.
    env.PassEnv(r'CVS.*|SSH_.*|GIT_.*')

    # The global tools will be keyed by directory path, so they will only
    # be applied to Environments contained within that path.  Make the path
    # key absolute since sometimes sub-projects may be out of the current
    # tree.  We also have to store the key in the environment, since later
    # on we may need the key to resolve the global tools, but at that point
    # there is no longer a way to retrieve the directory in which the
    # environment was created.

    gkey = env.Dir('.').get_abspath()
    env['GLOBAL_TOOLS_KEY'] = gkey
    if not _global_tools.has_key(gkey):
        _global_tools[gkey] = []

    if env.has_key('GLOBAL_TOOLS'):
        newtools = env['GLOBAL_TOOLS']
        Debug("Adding global tools @ %s: %s" % (gkey, str(newtools)), env)
        _global_tools[gkey].extend(newtools)
    # Now find every global tool list for parents of this directory.  Sort
    # them so that parent directories will appear before subdirectories.
    dirs = [k for k in _global_tools.keys() if gkey.startswith(k)]
    dirs.sort()
    gtools = []
    for k in dirs:
        for t in _global_tools[k]:
            if t not in gtools:
                gtools.append(t)
    Debug("Applying global tools @ %s: %s" %
          (gkey, ",".join([str(x) for x in gtools])), env)
    env.Require(gtools)
    return env


