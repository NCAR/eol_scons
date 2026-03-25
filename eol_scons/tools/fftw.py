# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

def generate(env):
    # Hardcode the selection of the threaded fftw3, and assume it's installed
    # somewhere already on the include path, ie, in a system path.
    env.Append(LIBS=['fftw3_threads', 'fftw3'])


def exists(env):
    return True
