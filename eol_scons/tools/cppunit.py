import sys
import os

def generate(env):
    # Don't try here to make things unique in LIBS and CFLAGS; just do a 
    # simple append
    try:
        env.ParseConfig('cppunit-config --cflags --libs', unique = False)
    except Exception, e:
        print "Unable to run cppunit-config. Cannot load tool cppunit."
        sys.exit(1) 
    # needed for FC2
    env.AppendLibrary("dl")



def exists(env):
    import subprocess
    try:
        subprocess.call('cppunit-config')
        return True
    except:
        return False

