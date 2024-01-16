# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
import os
import os.path


def generate(env):
    env.Append(LIBS=['forayutil',])

    libpath = os.path.join(env['OPT_PREFIX'], 'foray', 'lib')
    env.AppendUnique(LIBPATH=[libpath,])

    inc_path = os.path.join(env['OPT_PREFIX'], 'foray', 'include')
    env.AppendUnique(CPPPATH=[inc_path,])


def exists(env):
    return True
