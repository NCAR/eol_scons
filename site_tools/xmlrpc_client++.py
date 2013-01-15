# Tool for xmlrpc-c client with C++ interface
# Docs for the API are available at http://xmlrpc-c.sourceforge.net/
import os
import SCons.Errors

def generate(env):
    cmd = 'pkg-config --libs --cflags xmlrpc_client++'
    env.ParseConfig(cmd)

def exists(env):
    status = os.system('pkg-config --exists xmlrpc_client++')
    return(status == 0)

