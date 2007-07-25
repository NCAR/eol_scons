# -*- python -*-
import os

options = None

def generate(env):
  global options
  if not options:
    options = env.GlobalOptions()
    options.Add('BOOST_DIR',
"""Set the BOOST installation directory.  Otherwise the default
 is to use the system location.  Specify BOOST_DIR=/usr to force
 the system installation even when a boost directory is found in
 OPT_PREFIX.""",
    env.FindPackagePath('BOOST_DIR', '$OPT_PREFIX/boost*'))
  options.Update(env)
  env.Append(DEPLOY_SHARED_LIBS='boost_date_time')
  env.Append(DEPLOY_SHARED_LIBS='boost_serialization')
  if env.has_key('BOOST_DIR'):
    bdir=env['BOOST_DIR']
    if bdir and bdir != "/usr" and bdir != "":
      env.Append(CPPPATH=os.path.join(bdir,"include"));
      env.Append(LIBPATH=os.path.join(bdir,"lib"));
      env.Append(_LIBFLAGS=["-Wl,-R", os.path.join(bdir,"lib")]);

def exists(env):
  return True
