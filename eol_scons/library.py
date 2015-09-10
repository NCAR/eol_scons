# -*- python -*-
# Copyright 2007 UCAR, NCAR, All Rights Reserved

"""
The eol_scons package for EOL extensions to standard SCons.
"""

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


