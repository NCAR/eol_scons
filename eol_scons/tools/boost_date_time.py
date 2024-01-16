# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

def generate(env):
    env.Tool('boost')
    env.AppendBoostLibrary('boost_date_time')

def exists(env):
    return True

