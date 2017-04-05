# OpenMotif - Linux/Mac, no Windows.

import os, os.path

def generate(env):
  env.Append(LIBS=['Xm','Xt','X11'])
  if env['PLATFORM'] == 'darwin':
    env.Append(CPPPATH=['/opt/X11/include'])
    env.Append(LIBPATH=['/opt/X11/lib'])

def exists(env):
    return True
