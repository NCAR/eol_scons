# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

import SCons.Tool
import SCons.Tool.msvc

def Debug(env):
    env.Append(CCFLAGS=['/Zi'])
    return env

def Warnings(env):
    # env.Append(CCFLAGS='/Wall')
    env.Append(CCFLAGS=['/W2'])
    if 'NOUNUSED' in env:
        pass
    return env

def Optimize(env):
    env.Append(CCFLAGS=['/O2'])
    return env

def Profile(env):
    return env

def generate(env):
    SCons.Tool.msvc.generate(env)
    env.AddMethod(Optimize)
    env.AddMethod(Debug)
    env.AddMethod(Warnings)
    env.AddMethod(Profile)

def exists(env):
    return SCons.Tool.msvc.exists(env)
