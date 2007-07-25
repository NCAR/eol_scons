# -*- python -*-
import os,os.path

def generate(env):
  # Hardcode the selection of the threaded fftw3, and assume it's installed
  # somewhere already on the include path, ie, in a system path.
  env.Append(LIBS=['fftw3_threads','fftw3'])


def exists(env):
    return True

