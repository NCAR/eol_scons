# -*- python -*-
import os,os.path

def generate(env):
  
  libpath= os.path.join(env['OPT_PREFIX'],'lib')
  env.Append(LIBPATH=libpath) 
  env.Append(RPATH=libpath)
  env.Append(LIBS=['boost_python-gcc-1_32',])


def exists(env):
    return True

