# -*- python -*-
# Copyright 2007 UCAR, NCAR, All Rights Reserved

"""Tool methods invoked when eol_scons is loaded as a tool.
"""

import eol_scons.tool

def exists(env):
    return 1

def generate(env, **kw):
    """Generate the basic eol_scons customizations for the given
    environment, especially applying the scons built-in default tool
    and the eol_scons global tools."""

    eol_scons.tool.generate(env,**kw)

