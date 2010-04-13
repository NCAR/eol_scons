# GNU Scientific Library.

import os, os.path

def generate(env):
  env.Append(LIBS=['gsl','gslcblas','m'])


def exists(env):
    return True

