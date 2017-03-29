# OpenMotif - Linux/Mac, no Windows.

import os, os.path

def generate(env):
  env.Append(LIBS=['Xm','Xt','X11','Xext'])
  if env['PLATFORM'] == 'darwin':
    env.Append(CPPPATH=['/opt/X11/include'])
    env.Append(LIBPPATH=['/opt/X11/lib'])

def exists(env):
    return True
