# -*- python -*-
import os,os.path
import eol_scons
from SCons.Variables import PathVariable

_options = eol_scons.GlobalVariables()
_options.AddVariables(PathVariable('VXCONFIGDIR', 'VxWorks configuration dir.', 
                                   '/net/vx/config/eldora.tp41'))

def generate(env):
  _options.Update(env)
  env.Append(CPPPATH = ["$VXCONFIGDIR"])

def exists(env):
    return True

