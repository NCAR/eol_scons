# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

# Start of a primitive tool to experiment with boost logging.  Lots of
# hard-coded decisions here.

def generate(env):
    env.Tool('boost')
    env.AppendBoostLibrary('boost_log_setup')
    env.AppendBoostLibrary('boost_log')
    env.AppendBoostLibrary('boost_thread')
    env.Append(LIBS=['pthread'])
    env.AppendUnique(CPPDEFINES=['BOOST_LOG_DYN_LINK'])

def exists(env):
    return True

