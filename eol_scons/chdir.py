# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
import os
from SCons.Action import ActionFactory


def mkdir_if_missing(path):
    try:
        os.makedirs(path)
    except OSError:
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
