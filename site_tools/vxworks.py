# -*- python -*-
import os,os.path
import eol_scons
from SCons.Options import PathOption

_options = eol_scons.Pkg_Options()
_options.AddOptions(PathOption('VXCONFIGDIR', 'VxWorks configuration dir.', 
                               '/net/vx/config/eldora.tp41'))

def generate(env):
  _options.Update(env)
  env.Append(CPPPATH = ["$VXCONFIGDIR"])

def exists(env):
    return True

