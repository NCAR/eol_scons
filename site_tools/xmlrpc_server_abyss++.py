# Tool for xmlrpc-c Abyss server with C++ interface
# Docs for the API are available at http://xmlrpc-c.sourceforge.net/
import os
import SCons.Errors

def generate(env):
    # Use pkg-config to get C flags and libraries
    cmd = 'pkg-config --cflags --libs xmlrpc_server_abyss++'
    status = env.ParseConfig(cmd)

def exists(env):
    status = os.system('pkg-config --exists xmlrpc_server_abyss++')
    return(status == 0)

