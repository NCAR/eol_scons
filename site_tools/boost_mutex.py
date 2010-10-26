import os,os.path, sys
import SCons

# Use this tool for all Boost mutex classes (I'm using it for 
# boost::recursive_mutex); the Boost mutex classes depend on libpthread...
def generate(env):
    env.Append(LIBS=['pthread',])

def exists(env):
    return True
