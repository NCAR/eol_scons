from __future__ import print_function
import SCons

# As of 4/2014, this tool is deprecated; use the boost_thread tool instead.
#
# Use this tool for all Boost mutex classes (I'm using it for 
# boost::recursive_mutex). The mutex classes always require libpthread,
# and depending on Boost version, may also require libboost_thread.
warned = False

def generate(env):
    # We now just use the boost_thread tool to get boost::mutex support.
    env.Require(['boost_thread'])
    global warned
    if not warned:
        print('\nWARNING: The boost_mutex SCons tool is deprecated; switch to boost_thread.\n')
        warned = True

def exists(env):
    return True
