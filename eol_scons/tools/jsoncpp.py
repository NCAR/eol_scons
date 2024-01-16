# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
import eol_scons.parseconfig as pc

def generate(env):
    pc.ParseConfig(env, 'pkg-config --cflags --libs jsoncpp')

def exists(env):
    return True

