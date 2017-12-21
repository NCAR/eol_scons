# -*- python -*-
import os,os.path, SCons
from py_compile import compile
import py_compile 
from SCons.Environment import Environment

from eol_scons.chdir import mkdir_if_missing
# eventually, we may need a way to override this,
# for now, assume that all paths
# are relative to the python executable used by 'scons'
#from distutils import sysconfig
#PYTHON_SITE_DIR=sysconfig.get_python_lib()


def generate(env):
  python= 'python2.4'

  def compilePython(target, source, env):
     t0 = target[0]
     file = t0.abspath
     #  print 'Compiling  ', file
     py_compile.compile(file)


#  def InstallPythonScripts(self, libDir):
  def InstallPythonScripts(env, libDir):
     from glob import glob1
     mkdir_if_missing(libDir)
     pylist = glob1('.', '*.py')
     env.Install(libDir, pylist)
     for p in pylist:
        env.AddPostAction(os.path.join(libDir, p), compilePython)

  opt= env.get('OPT_PREFIX', '$DEFAULT_OPT_PREFIX')
  PYTHON_SITE_DIR=os.path.join(opt, 'lib', python,'site-packages')
  env["PYTHON_SITE_DIR"] = PYTHON_SITE_DIR
  #env.Append(CPPPATH=[sysconfig.get_python_inc(), ])
  env.Append(CPPPATH=[os.path.join(opt,'include',python), ])
  #env.Append(LIBPATH=[os.path.join(sysconfig.get_python_lib(standard_lib=1),  'config'), ])
  env.Append(LIBPATH=[os.path.join(opt,'lib',python,  'config'), ])
  env.Append(LIBS=[python, ])
  Environment.InstallPythonScripts = InstallPythonScripts


def exists(env):
    return True

