# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

def generate(env):
    """
    Tool for the legacy netcdf-c++ library.
    """
    env.Append(LIBS=['netcdf_c++'])
    env.Require('netcdf')


def exists(env):
    return True
