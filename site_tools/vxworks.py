# -*- python -*-
import os,os.path
import eol_scons
from SCons.Options import PathOption

options = eol_scons.Pkg_Options()
options.AddOptions (PathOption('VXDIR', 'VxWorks root directory.', '/vx'))

def generate(env):
  options.Update(env)
  #env.Append(CPPPATH = ["$VXDIR/h"])
  #env.Append(CPPPATH = ["$VXDIR/h", "$VXDIR/config/tp41"])


def exists(env):
    return True

