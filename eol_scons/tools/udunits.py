# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

def generate(env):
    # Look for udunits, and if not found look for udunits2.  We need a
    # clean environment, though, else other LIBS can cause link problems.
    ckenv = env.Clone()
    ckenv['LIBS'] = []
    conf = ckenv.Configure()
    if conf.CheckLib('udunits'):
        env.Append(LIBS=['udunits'])
    elif conf.CheckLib('udunits2'):
        env.Append(LIBS=['udunits2'])
        env.Append(CPPPATH=['/usr/include/udunits2'])
    ckenv = conf.Finish()


def exists(env):
    return True
