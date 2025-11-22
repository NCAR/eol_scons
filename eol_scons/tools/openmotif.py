# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

# OpenMotif - Linux/Mac, no Windows.

def generate(env):
    env.Append(LIBS=['Xm', 'Xt', 'X11'])


def exists(env):
    return True
