import os
import re
import subprocess
import SCons.Errors
import SCons

def Kmake(env,target,source):

    if not env.has_key('KERNELDIR') or env['KERNELDIR'] == '':
	    print "KERNELDIR not specified, " + target[0].abspath + " will not be built"
            return None

    if not os.path.exists(env['KERNELDIR']):
        print 'Error: KERNELDIR=' + env['KERNELDIR'] + ' not found.'

    # Have the shell subprocess do a cd to the source directory.
    # If scons/python does it, then the -j multithreaded option doesn't work.
    srcdir = os.path.dirname(source[0].abspath)
    return env.Execute('cd ' + srcdir + '; ' + env['KMAKE'])

def generate(env):

    k = env.Builder(action=Kmake,
                    source_scanner=SCons.Tool.SourceFileScanner)
    env.Append(BUILDERS = {'Kmake':k})

def exists(env):
    return True
