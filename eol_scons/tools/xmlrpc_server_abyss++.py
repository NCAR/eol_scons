# Tool for xmlrpc-c Abyss server with C++ interface
# Docs for the API are available at http://xmlrpc-c.sourceforge.net/
import os
import SCons.Errors
import subprocess

def generate(env):
    # Use pkg-config to get C flags and libraries
    cmd = 'pkg-config --cflags --libs xmlrpc_server_abyss++'
    try:
        status = env.ParseConfig(cmd)
    except OSError:
        print "Error loading tool xmlrpc_server_abyss++:", sys.exc_info()[0]
        print "Have you installed package 'xmlrpc-c-devel' (or similar)?"
        raise SCons.Errors.StopError

def exists(env):
    status = subprocess.Popen(['pkg-config', 'xmlrpc_server_abyss++'],
                              env=env['ENV']).wait()
    return status == 0

