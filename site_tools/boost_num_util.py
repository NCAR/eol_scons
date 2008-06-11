# -*- python -*-
import os,os.path
import string

def generate(env):
  numUtilDir = os.path.abspath(os.path.join(env['OPT_PREFIX'],
                                            'perp_depend',
                                            'boost__deps', 
                                            'num_util'))
  env.Append(CPPPATH=[ numUtilDir, ])
  env.Append(LIBPATH=[ numUtilDir, ])
  env.Append(LIBS=['num_util',])
  env.Append(CCFLAGS=string.split("""
  -pthread -fno-strict-aliasing -Wall -fno-inline  -ftemplate-depth-100
  -DBOOST_PYTHON_DYNAMIC_LIB 
  -DBOOST_PYTHON_V2"""))


def exists(env):
    return True

