import os
import SCons
from SCons.Action import ActionFactory

Chdir = ActionFactory(os.chdir, lambda dir: 'Chdir("%s")' % (dir))

def mkdir_if_missing(dir):
    try:
        os.makedirs(dir)
    except:
        pass

MkdirIfMissing = ActionFactory(mkdir_if_missing,
                               lambda dir: 'Mkdir("%s")' % dir)

def ChdirActions(env, actions, dir = None):
    """Run a list of actions in a certain directory by surrounding the
    list with Chdir actions to change into and out of the directory."""
    if not dir:
        dir = env.Dir('.').path
    return [ Chdir(dir) ] + actions + [ Chdir(env.Dir("#").get_abspath()) ]

if 0:

    env = Environment()

    Execute(Chdir("/tmp"))
    print os.getcwd()
