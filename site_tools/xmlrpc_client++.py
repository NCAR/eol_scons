# Tool for xmlrpc-c client with C++ interface
# Docs for the API are available at http://xmlrpc-c.sourceforge.net/
import os
import SCons.Errors

def generate(env):
    cmd = 'pkg-config --libs --cflags xmlrpc_client++'
    try:
        env.ParseConfig(cmd)
    except OSError as err:
        print "Error loading tool xmlrpc_client++:", err
        print "Have you installed package 'xmlrpc-c-devel' (or similar)?"
        raise SCons.Errors.StopError

def exists(env):
    status = os.system('pkg-config --exists xmlrpc_client++')
    return(status == 0)

