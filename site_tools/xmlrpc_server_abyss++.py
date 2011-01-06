import sys
import os

# We just use xmlrpc-c-config to get what we need
config_cmd = 'xmlrpc-c-config c++2 abyss-server'

def generate(env):
    try:
        env.ParseConfig(config_cmd + " --cflags", unique = False)
        env.ParseConfig(config_cmd + " --libs", unique = False)
    except Exception, e:
        print "Unable to run '" + config_cmd + "'. Cannot load tool xmlrpc_server_abyss++."
        sys.exit(1)

def exists(env):
    import subprocess
    try:
        subprocess.call(config_cmd + " --prefix")
        return True
    except:
        return False

