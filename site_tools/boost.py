# -*- python -*-
import os
import SCons.Util

options = None

liblibs = [ 'boost_unit_test_framework',
            'boost_prg_exec_monitor',
            'boost_test_exec_monitor',
            'boost_wave' ]

def boost_libflags(env):
  newlibs = []
  for lib in env['LIBS']:
    if SCons.Util.is_String(lib) and \
           lib.startswith("boost_") and \
           not lib.endswith("$BOOST_LIBRARY_SUFFIX"):
      if env['PLATFORM'] == 'win32' and lib in liblibs:
          lib = 'lib'+lib
      newlibs.append(lib+"$BOOST_LIBRARY_SUFFIX")
    else:
      newlibs.append(lib)
  env['LIBS'] = newlibs
  result = env.subst(env['_boost_save_libflags'])
  return result

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
  if not env.has_key('BOOST_LIBRARY_SUFFIX'):
    if env['PLATFORM'] == 'win32':
      env['BOOST_LIBRARY_SUFFIX'] = '-vc71-mt-gd-1_33_1'
    else:
      env['BOOST_LIBRARY_SUFFIX'] = ''
  if env.has_key('BOOST_DIR'):
    bdir=env['BOOST_DIR']
    if bdir and bdir != "/usr" and bdir != "":
      env.Append(CPPPATH=os.path.join(bdir,"include"));
      # Windows installs don't have a separate include directory.
      env.Append(CPPPATH=os.path.join(bdir));
      env.AppendUnique(LIBPATH=os.path.join(bdir,"lib"));
      env.AppendUnique(RPATH=[os.path.join(bdir,"lib")]);
  # Override the _LIBFLAGS variable so we can append the suffix for
  # boost libraries.
  if not env.has_key('_boost_save_libflags'):
    env["_boost_save_libflags"] = env["_LIBFLAGS"]
    env['_LIBFLAGS'] = '${_boost_libflags(__env__)}'
    env['_boost_libflags'] = boost_libflags


def exists(env):
  return True
