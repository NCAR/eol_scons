#
# Tool for RAL's radar library.
#
    
import os
import string
import re
import SCons
from eol_scons.chdir import ChdirActions
from SCons.Variables import PathVariable

_options = None
mykey = "HAS_PKG_RAP_RADAR"

def generate(env):

  global _options
  if not _options:
    _options = env.GlobalVariables()
    _options.Add('RAP_ROOT', 
        'Root directory for RAP library installation.', 
        os.path.join(env.subst('$OPT_PREFIX'), 'rap'))

  _options.Update(env)
 
  if not env.has_key(mykey):

    rap_root = env['RAP_ROOT']
        
    inc_path = os.path.join(rap_root, 'include')
    if not os.path.exists(inc_path):
        raise SCons.Errors.StopError, ("Directory '" + inc_path + 
            "' does not exist for package rap_radar!  Try setting RAP_ROOT.")
    env.AppendUnique(CPPPATH=[inc_path])
    
    lib_path = os.path.join(rap_root, 'lib')
    if not os.path.exists(lib_path):
        raise SCons.Errors.StopError, ("Directory '" + lib_path + 
            "' does not exist for package rap_radar!  Try setting RAP_ROOT.")
    env.Append(LIBPATH=[lib_path])
    
    # Here's the actual library
    libs = ['radar']
    env.Append(LIBS=libs)
    
    # The RAL radar library needs the fftw package as well
    env.Require('fftw')

    env[mykey] = 1


def exists(env):
    return True