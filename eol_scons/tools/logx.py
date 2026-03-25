# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.


def generate(env):
    # include and lib paths are expected to already be part of the
    # default setup, either under the OPT_PREFIX or under the top
    # source directory.
    #
    # env.Append(LIBPATH= ['#/logx',])
    # env.Append(LIBS=['logx',])
    env.AppendLibrary("logx")
    env.Tool('log4cpp')


def exists(env):
    return True
