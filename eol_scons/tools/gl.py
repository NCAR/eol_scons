
import os, os.path

def generate(env):
  env.Append(LIBS=['glut','GLU','GL','Xmu','Xi'])


def exists(env):
    return True

