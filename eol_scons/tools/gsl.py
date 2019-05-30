# GNU Scientific Library.

import os, os.path

def generate(env):
  env.Append(LIBS=['gsl','gslcblas'])
  if env['PLATFORM'] != 'msys':
    env.Append(LIBS=['m'])


def exists(env):
    return True

