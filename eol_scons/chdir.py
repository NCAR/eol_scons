# -*- python -*-
# Copyright 2007 UCAR, NCAR, All Rights Reserved

import os
from SCons.Action import ActionFactory

def mkdir_if_missing(path):
    try:
        os.makedirs(path)
    except:
        pass

MkdirIfMissing = ActionFactory(mkdir_if_missing,
                               lambda p: 'Mkdir("%s")' % p)

def ChdirActions(env, actions, path=None):
    """Run a list of actions in a certain directory"""
    if not path:
        path = env.Dir('.').path
    cdActions = []
    for cmd in actions:
        cdActions += ["cd %s && %s" % (path, cmd)]
    return cdActions

