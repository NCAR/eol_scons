import os
import re
import subprocess
import SCons.Errors
import SCons

from subprocess import Popen,PIPE

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

    if not env.has_key('KERNELDIR') or env['KERNELDIR'] == '*':
        krel = Popen(['uname','-r'],stdout=PIPE).communicate()[0].rstrip("\n")
        # How to build KERNELDIR from uname:
        # EL5, i686, PAE: (merlot)
        #   uname -r: 2.6.18-164.9.1.el5PAE
        #   uname -m: i686
        #   kernel-devel path: /usr/src/kernels/2.6.18-164.9.1.el5-i686
        #   For KERNELDIR, must remove "PAE" from `uname -r`, append '-' + `uname -m`
        # EL5, x86_64: (shiraz)
        #   uname -r: 2.6.18-164.6.1.el5
        #   uname -m: x86_64
        #   kernel-devel path: /usr/src/kernels/2.6.18-64.el5-x86_64
        #   KERNELDIR is /usr/src/kernels/`uname -r` + '-' + `uname -m`
        # Fedora 11, i686, PAE (need package: kernel-PAE-devel)
        #   uname -r: 2.6.30.10-105.fc11.i686.PAE
        #   uname -m: i686
        #   kernel-PAE-devel path: /usr/src/kernels/2.6.30.10-105.fc11.i686.PAE
        #   KERNELDIR is /usr/src/kernels/`uname -r`
        #
        kdir = '/usr/src/kernels/' + krel
        if not os.path.exists(kdir):
            kmach = Popen(['uname','-m'],stdout=PIPE).communicate()[0].rstrip("\n")
            kdir = '/usr/src/kernels/' + krel + '-' + kmach
            if not os.path.exists(kdir):
                # Remove PAE or xen from uname -r output
                krel = krel.replace("xen","")
                krel = krel.replace("PAE","")
                kdir = '/usr/src/kernels/' + krel + '-' + kmach
        env['KERNELDIR'] = kdir
        print 'KERNELDIR set to ' + env['KERNELDIR']

    # If KERNELDIR doesn't exist, issue a warning here and let it fail later.
    if not os.path.exists(env['KERNELDIR']):
            print 'Error: KERNELDIR=' + env['KERNELDIR'] + ' not found. Suggestion: install the kernel-devel or kernel-PAE-devel package, and use KERNELDIR=\'*\'.'

    if not env.has_key('KINCLUDE'):
        env['KINCLUDE'] = env.Dir("#").get_abspath()

    if not env.has_key('KMAKE'):
        env['KMAKE'] = "make KERNELDIR=$KERNELDIR KINCLUDE=$KINCLUDE"

    k = env.Builder(action=Kmake,
                    source_scanner=SCons.Tool.SourceFileScanner)
    env.Append(BUILDERS = {'Kmake':k})

def exists(env):
    return env.Detect(['gcc','g++'])

