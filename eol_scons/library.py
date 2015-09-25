# -*- python -*-
# Copyright 2007 UCAR, NCAR, All Rights Reserved

"""
The eol_scons package for EOL extensions to standard SCons.
"""

import SCons.Tool
from SCons.Builder import BuilderBase
from SCons.Builder import _null

from eol_scons.debug import Debug

class _LibraryBuilder(BuilderBase):
    """
    This class should allow for equivalent instances to the builder created
    by SCons.Tool.createStaticLibBuilder, as long as the right Builder
    keywords are propagated to the BuilderBase subclass.  The only
    difference in the subclass instance should be the __call__ method to
    intercept the library target.
    """

    def __init__(self, builder):
        BuilderBase.__init__(self, 
                             action=builder.action,
                             emitter=builder.emitter,
                             prefix=builder.prefix,
                             suffix=builder.suffix,
                             src_suffix=builder.src_suffix,
                             src_builder=builder.src_builder)

    def __call__(self, env, target=None, source=None, chdir=_null, **kw):
        "Override __call__ from the base class to register the target library."
        Debug("_LibraryBuilder.__call__ for target(%s)" % (target), env)
        ret = BuilderBase.__call__(self, env, target, source, chdir, **kw)
        if target:
            env.AddLibraryTarget(target, ret)
        else:
            Debug("library builder returned None!", env)
        return ret

def _library_builder_str(env):
    t = "[env.Library=%s, builder=%s]"
    try:
        libmethod = env.Library
    except AttributeError:
        libmethod = "None"
    return t % (libmethod, env.get_builder('Library'))


def ReplaceLibraryBuilders(env):

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

    env.LogDebug("Replacing standard library builders with subclass")
    builder = SCons.Tool.createStaticLibBuilder(env)
    builder = _LibraryBuilder(builder)
    env['BUILDERS']['StaticLibrary'] = builder
    env['BUILDERS']['Library'] = builder
    builder = SCons.Tool.createSharedLibBuilder(env)
    builder = _LibraryBuilder(builder)
    env['BUILDERS']['SharedLibrary'] = builder

    # Debug("After wrapping Library: %s" % (_library_builder_str(env)))

