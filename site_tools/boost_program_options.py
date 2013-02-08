import os,os.path, sys
import SCons

def has_boost_system(env, libname):
    """See if boost::system is available. It was introduced
    in Boost v1.35, and so is not found on RHEL5 systems.
    We try to compile a program which references boost::system::error_code.
    
    Returns: True if found, False if not.
    """
    
    # Define the test program
    header = 'boost/system/error_code.hpp'
    test_src = 'boost::system::error_code code;'

    # Try to build it
    conf = env.Clone(LIBS=[]).Configure()
    has_it = conf.CheckLibWithHeader(libname, header, 'CXX', test_src)
    conf.Finish()

    return has_it

def generate(env):

    if env['PLATFORM'] != 'darwin':
        env.Append (LIBS = ["boost_program_options"])
        if has_boost_system(env, "boost_system"):
            env.Append (LIBS = ["boost_system"])
    else:
        env.Append (LIBS = ["boost_program_options-mt"])
        if has_boost_system(env, "boost_system-mt"):
            env.Append (LIBS = ["boost_system-mt"])
                
    libpath = os.path.abspath(os.path.join(env['OPT_PREFIX'], 'lib'))
    env.AppendUnique(LIBPATH=[libpath])

def exists(env):
    return True

