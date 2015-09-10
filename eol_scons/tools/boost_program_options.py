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
    if env['PLATFORM'] == 'darwin':
        libname = libname + '-mt'

    # Try to build it
    conf = env.Clone(LIBS=[]).Configure()
    has_it = conf.CheckLibWithHeader(libname, header, 'CXX', test_src)
    conf.Finish()
    return has_it

def generate(env):
    env.Tool('boost')
    env.AppendBoostLibrary('boost_program_options')
    if has_boost_system(env, 'boost_system'):
        env.AppendBoostLibrary ('boost_system')

def exists(env):
    return True

