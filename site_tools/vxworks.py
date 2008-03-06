# -*- python -*-
import os,os.path
import eol_scons
from SCons.Options import PathOption

options = eol_scons.Pkg_Options()
options.AddOptions(PathOption('VXCONFIGDIR', 'VxWorks configuration dir.', 
                              '/net/vx/config/eldora.tp41'))

def generate(env):
  options.Update(env)
  env.Append(CPPPATH = ["$VXCONFIGDIR"])

def exists(env):
    return True

