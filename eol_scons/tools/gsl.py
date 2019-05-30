# GNU Scientific Library.

import os, os.path

def generate(env):
  env.Append(LIBS=['gsl','gslcblas'])
  # On msys the math functions come in via libmsvcrt.a, and there will be
  # multiple definitions if add -lm.
  if env['PLATFORM'] != 'msys':
    env.Append(LIBS=['m'])


def exists(env):
    return True

