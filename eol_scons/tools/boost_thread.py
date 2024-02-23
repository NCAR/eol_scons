# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
"""
Use this tool for Boost thread support.
"""

import SCons


# Once we've found the lib(s), keep a global copy for future loads of the
# module
Libs = None

# Required libraries for Boost threads have changed a lot over time.  For
# older versions of Boost mutexes, we need to link with both boost_thread and
# pthread libraries. Also, some versions have separate multi-threaded
# instances of Boost libraries, leaving the need to check for
# libboost_thread-mt vs. libboost_thread. Use Environment.Configure to test
# which way will work on this system.

# Try, in order:
#  -lboost_thread-mt
#  -lboost_thread
#  -lpthread   <-- I don't know if any config works with only -lpthread...
#  -lboost_thread-mt -lpthread
#  -lboost_thread -lpthread
# to see if any combination will work. If not, complain and quit.


def generate(env):
    # Don't go any further if they're cleaning or asked for help
    if env.GetOption('clean') or env.GetOption('help'):
        return

    # Use the previously found lib(s) if possible, otherwise use
    # Environment.Configure to figure out what we need.
    global Libs
    if not Libs:
        clonedEnv = env.Clone()
        clonedEnv.Replace(LIBS=[])
        conf = clonedEnv.Configure()

        header = 'boost/thread/thread.hpp'
        test_src = 'boost::thread bt; boost::thread::id bt_id = bt.get_id();'
        test_libs = ['boost_thread-mt', 'boost_thread', 'pthread']
        found = conf.CheckLibWithHeader(test_libs, header, 'CXX', test_src)
        if not found:
            # Bare libraries didn't work. Try again with -lpthread added to
            # the mix.
            clonedEnv.Append(LIBS='pthread')
            test_libs = ['boost_thread-mt', 'boost_thread']
            found = conf.CheckLibWithHeader(test_libs, header, 'CXX', test_src)
        conf.Finish()
        if not found:
            msg = "No working boost_thread library configuration found. "
            msg += "Check config.log."
            raise SCons.Errors.StopError(msg)

        # Save the lib(s) we found to work
        Libs = clonedEnv['LIBS']

    env.Append(LIBS=Libs)


def exists(env):
    return True
