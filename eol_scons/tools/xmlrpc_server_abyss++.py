"""
Tool for xmlrpc-c Abyss server with C++ interface.  Docs for the API
are available at http://xmlrpc-c.sourceforge.net/.
"""

import sys
import SCons.Errors
import eol_scons.parseconfig as pc

def generate(env):
    # Use pkg-config to get C flags and libraries
    #
    # At least for CentOS 7, we need the --static flag on pkg-config to get
    # the complete list of needed libraries for the xmlrpc-c packages
    cmd = 'pkg-config --static --cflags --libs xmlrpc_server_abyss++'
    if not pc.ParseConfig(env, cmd):
        print("Error loading tool xmlrpc_server_abyss++:", sys.exc_info()[0])
        print("Have you installed package 'xmlrpc-c-devel' (or similar)?")
        raise SCons.Errors.StopError

def exists(env):
    return pc.CheckConfig(env, 'pkg-config xmlrpc_server_abyss++')

