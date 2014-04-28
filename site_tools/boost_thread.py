import os,os.path, sys
import SCons


# Use this tool for Boost thread support

# Once we've found the lib(s), keep a global copy for future loads of the module
Libs = None

# Required libraries for Boost threads have changed a lot over time.
# For older versions of Boost mutexes, we need to link with both
# boost_thread and pthread libraries. Also, some versions have separate
# multi-threaded instances of Boost libraries, leaving the need to check for
# libboost_thread-mt vs. libboost_thread. Use Environment.Configure to test 
# which way will work on this system.
# Try, in order:
#       -lboost_thread-mt
#       -lboost_thread
#       -lpthread
#       -lboost_thread-mt -lpthread
#       -lboost_thread -lpthread
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
        # Disable SConf display of messages like "Checking for <x> in <y>..."
        origPrintState = SCons.SConf.progress_display.print_it
        SCons.SConf.progress_display.print_it = False
    
        header = 'boost/thread/thread.hpp'
        test_src = 'boost::thread bt; boost::thread::id bt_id = bt.get_id();'
        test_libs = ['boost_thread-mt', 'boost_thread', 'pthread']
        if (not conf.CheckLibWithHeader(test_libs, header, 'CXX', test_src)):
            # Bare libraries didn't work. Try again with -lpthread added to the mix.
            clonedEnv.Append(LIBS = 'pthread')
            test_libs = ['boost_thread-mt', 'boost_thread']
            if (not conf.CheckLibWithHeader(test_libs, header, 'CXX', test_src)):
                msg = "No working boost_thread library configuration found. "
                msg += "Check config.log."
                raise SCons.Errors.StopError, msg
            
        conf.Finish()
        
        # Restore SConf's print state
        SCons.SConf.progress_display.print_it = origPrintState
        
        # Save the lib(s) we found to work
        Libs = clonedEnv['LIBS']
    
    env.Append(LIBS=Libs)
    

def exists(env):
    return True
