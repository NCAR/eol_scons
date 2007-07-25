# GNU Scientific Library.

import os, os.path

def generate(env):
  env.Append(DEPLOY_SHARED_LIBS=['gsl','gslcblas'])
  env.Append(LIBS=['gsl','gslcblas','m'])


def exists(env):
    return True

