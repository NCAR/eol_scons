"""
Tool for xmlrpc-c client with C++ interface.  Docs for the API are
available at http://xmlrpc-c.sourceforge.net/.
"""
from __future__ import print_function
import os
import SCons.Errors
import eol_scons.parseconfig as pc

def generate(env):
    cmd = 'pkg-config --libs --cflags xmlrpc_client++'
    if not pc.ParseConfig(env, cmd):
        print("Error loading tool xmlrpc_client++:", sys.exc_info()[0])
        print("Have you installed package 'xmlrpc-c-devel' (or similar)?")
        raise SCons.Errors.StopError

def exists(env):
    return pc.CheckConfig(env, 'pkg-config xmlrpc_client++')

