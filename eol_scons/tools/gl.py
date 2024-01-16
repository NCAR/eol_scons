# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

def generate(env):
    env.Append(LIBS=['glut', 'GLU', 'GL', 'Xmu', 'Xi'])


def exists(env):
    return True
