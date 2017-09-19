from __future__ import print_function
import sys
import os
import SCons.Errors
import eol_scons.parseconfig as pc

_cmd = 'cppunit-config --cflags --libs'

def generate(env):
    # Don't try here to make things unique in LIBS and CFLAGS; just do a 
    # simple append
    if not pc.ParseConfig(env, _cmd, unique=False):
        print("Unable to run cppunit-config. Cannot load tool cppunit.")
        raise SCons.Errors.StopError
    # needed for FC2
    env.AppendLibrary("dl")


def exists(env):
    return pc.CheckConfig(env, _cmd)
