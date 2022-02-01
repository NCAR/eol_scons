# OpenMotif - Linux/Mac, no Windows.

import os, os.path

def generate(env):
  env.Append(LIBS=['Xm','Xt','X11'])

def exists(env):
    return True
