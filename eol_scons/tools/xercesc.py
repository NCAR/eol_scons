# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

from pathlib import Path


def generate(env):

    # probably it's time for xerces-c to not depend on OPT_PREFIX.  maybe
    # XERCESC_PREFIX should be a global Variable, and probably pkg-config
    # should be used also.
    prefix = None
    if 'XERCESC_PREFIX' in env:
        prefix = env.subst(env['XERCESC_PREFIX'])
    elif 'OPT_PREFIX' in env:
        prefix = env.subst(env['OPT_PREFIX'])
        env['XERCESC_PREFIX'] = prefix
    env.Append(LIBS=['xerces-c'])
    if prefix and Path(prefix, 'lib', 'libxerces-c.so').exists():
        env.AppendUnique(LIBPATH=[str(Path(prefix, 'lib'))])
        env.AppendUnique(CPPPATH=[str(Path(prefix, 'include'))])


def exists(env):
    return True
