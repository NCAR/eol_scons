"""scons arm tool

Customize an environment to use the GCC ARM cross-compiler tools.
"""

import os
import re
import subprocess
import kmake
import localutils
import SCons.Tool

from subprocess import Popen,PIPE

def generate(env,**kw):

    env['KERNELDIR'] = kw.get('KERNELDIR','')

    if env['KERNELDIR'] == '*':
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

    # If KERNELDIR doesn't exist, issue a warning here and
    # let it fail later.
    if env['KERNELDIR'] != '':
        if os.path.exists(env['KERNELDIR']):
            print 'KERNELDIR=' + env['KERNELDIR'] + ' found'
        else:
            print 'Error: KERNELDIR=' + env['KERNELDIR'] + ' not found. Suggestion: install the kernel-devel or kernel-PAE-devel package, and use KERNELDIR=\'*\'.'

    env['KINCLUDE'] = env.Dir("#").get_abspath()
    env['KMAKE'] = "make KERNELDIR=$KERNELDIR KINCLUDE=$KINCLUDE"

    cxxrev = localutils.get_cxxversion(env)
    if cxxrev != None:
        env.Replace(CXXVERSION = cxxrev)

def exists(env):
    return env.Detect(['arm-linux-gcc','arm-linux-g++'])

