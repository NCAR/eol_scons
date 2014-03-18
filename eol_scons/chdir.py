import os
import SCons
from SCons.Action import ActionFactory

def mkdir_if_missing(dir):
    try:
        os.makedirs(dir)
    except:
        pass

MkdirIfMissing = ActionFactory(mkdir_if_missing,
                               lambda dir: 'Mkdir("%s")' % dir)

def ChdirActions(env, actions, dir = None):
    """Run a list of actions in a certain directory"""
    if not dir:
        dir = env.Dir('.').path
    cdActions = []
    for cmd in actions:
        cdActions += ["cd %s && %s" % (dir, env.subst(cmd))]
    return cdActions

if 0:

    env = Environment()

    Execute(Chdir("/tmp"))
    print os.getcwd()
