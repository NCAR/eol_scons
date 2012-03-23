"""scons x86 tool
Customize an environment for X86.
Sets the value of KMAKE, KERNELDIR and KINCLUDE for the Kmake builder
of Linux kernel modules. KERNELDIR and KINCLUDE are referenced in
the Makefile(s) that are used to build modules.
If passed a value of KERNELDIR="*" then this tool runs uname to
determine the path to the config and headers of the current kernel on
the localhost.  Packages kernel-devel and kernel-PAE-devel install
the kernel headers and config to /usr/src/kernels. This tool
should be able find them, but will need updating if the naming
convention in the packages changes.
If KERNELDIR is other than "*" then that value is used.
"""

import os
import re
import subprocess
import kmake
import localutils
import SCons.Tool

from subprocess import Popen,PIPE

def generate(env,**kw):

    if env.has_key('KERNELDIR') and env['KERNELDIR'] == '*':
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
    if env['KERNELDIR'] != '' and not os.path.exists(env['KERNELDIR']):
            print 'Error: KERNELDIR=' + env['KERNELDIR'] + ' not found. Suggestion: install the kernel-devel or kernel-PAE-devel package, and use KERNELDIR=\'*\'.'

    env['KINCLUDE'] = env.Dir("#").get_abspath()
    env['KMAKE'] = "make KERNELDIR=$KERNELDIR KINCLUDE=$KINCLUDE"

    cxxrev = localutils.get_cxxversion(env)
    if cxxrev != None:
        env.Replace(CXXVERSION = cxxrev)

def exists(env):
    return env.Detect(['gcc','g++'])

