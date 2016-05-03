# Tool for xmlrpc-c client with C++ interface
# Docs for the API are available at http://xmlrpc-c.sourceforge.net/
import os
import subprocess
import SCons.Errors

def generate(env):
    cmd = 'pkg-config --libs --cflags xmlrpc_client++'
    try:
        env.ParseConfig(cmd)
    except OSError:
        print "Error loading tool xmlrpc_client++:", sys.exc_info()[0]
        print "Have you installed package 'xmlrpc-c-devel' (or similar)?"
        raise SCons.Errors.StopError

def exists(env):
    status = subprocess.Popen(['pkg-config', 'xmlrpc_client++'],
                              env=env['ENV']).wait()
    return status == 0

