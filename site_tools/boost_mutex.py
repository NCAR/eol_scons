import os,os.path, sys
import SCons


# Use this tool for all Boost mutex classes (I'm using it for 
# boost::recursive_mutex). The mutex classes always require libpthread,
# and depending on Boost version, may also require libboost_thread.
def generate(env):
    # For older versions of Boost mutexes, we need to link with both
    # boost_thread and pthread libraries. For later versions, we only
    # need pthread. Use Environment.Configure to test which way will work
    # on this system.
    clone = env.Clone()
    clone.Replace(LIBS=[])
    conf = clone.Configure()
    header = 'boost/thread/mutex.hpp'
    test_src = 'boost::mutex m; boost::mutex::scoped_lock guard(m);'
    if (not conf.CheckLibWithHeader('pthread', header, 'CXX', test_src) and
        not conf.CheckLibWithHeader(['boost_thread', 'pthread'], header, 'CXX', test_src)):
            msg = "Failed to link to boost::mutex both with and without"
            msg += " libboost_thread.  Check config.log."
            raise SCons.Errors.StopError, msg

    conf.Finish()
        
    env.Append(LIBS=clone['LIBS'])

def exists(env):
    return True
