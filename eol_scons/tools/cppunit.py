# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
import SCons.Errors
import eol_scons.parseconfig as pc

_cmd = 'pkg-config --cflags --libs cppunit'


def generate(env):
    # Don't try here to make things unique in LIBS and CFLAGS; just do a
    # simple append
    if not pc.ParseConfig(env, _cmd, unique=False):
        print("cppunit not found: %s" % (_cmd))
        raise SCons.Errors.StopError


def exists(env):
    return pc.CheckConfig(env, _cmd)
