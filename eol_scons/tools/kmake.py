"""
SCons tool which provides a builder for Linux kernel modules.

You must provide a Makefile in the current directory, having the
usual syntax for Linux module Makefiles, where the object file names
of the desired modules are listed in the definition of the obj-m make variable.
This example shows how a module, my_mod2, can be built from multiple
source code files:

############################################################################
# if KERNELRELEASE is defined, we've been invoked from the
# kernel build system and can use its language
ifneq ($(KERNELRELEASE),)
        obj-m := my_mod1.o my_mod2.o
        my_mod2-objs := my_mod2_init.o mod2_other_code.o

# Otherwise we were called directly from the command
# line; invoke the kernel build system.
else
	KERNELDIR ?= /lib/modules/$(shell uname -r)/build
	PWD := $(shell pwd)

default:
	$(MAKE) -C $(KERNELDIR) M=$(PWD) CFLAGS_MODULE="-DMODULE $(KCFLAGS)" modules

endif
############################################################################

If you know the location of the kernel source tree to build your module against, 
set the value of KERNELDIR in the environment before loading this tool:

    kenv = env.Clone(tools=['kmake'],KERNELDIR='/usr/local/linux/kernel/2.6.42')

On RedHat systems, which have the kernel-devel package installed, this tool's generate
method will try to determine the value of KERNELDIR for you, using the uname command,
in which case you don't need to define KERNELDIR before loading the tool:

    kenv = env.Clone(tools=['kmake'])

The KMAKE construction variable is the command that is run to make the module.
If necessary it can be customized:
    kenv.Replace(KMAKE='make KERNELDIR=$KERNELDIR KCFLAGS="$KCFLAGS" ARCH=arm CROSS_COMPILE=arm-linux-')

The default value for KMAKE should be sufficient to build modules for the host system:
    KMAKE: "make KERNELDIR=$KERNELDIR KCFLAGS=$KCFLAGS"

The default value of KCFLAGS is the current source directory:
    KCFLAGS: '-I' + env.Dir("#").get_abspath()

Finally, to build the .ko files of the modules, do:
    kenv.Kmake(['my_mod1.ko','my_mod2.ko'],
          ['my_mod1.c','my_mod2_init.c','mod2_other_code.c','Makefile'])

TODO:
    The names of exported symbols in modules are written to Module.symvers files in each
    build directory during the module build.  If the Module.symvers files could be
    referred to in the builds of other modules that use the exported symbols we could
    avoid these warnings about undefined symbols:
    WARNING: "register_irig_callback" [.../build_arm/build_linux/build_ncar_a2d_titan/ncar_a2d.ko] undefined!

    See "6.3 Symbols From Another External Module" in the linux kernel docs: Documentation/kbuild/modules.txt

    One of the ways to refer to Module.symvers files is with the KBUILD_EXTRA_SYMBOLS env variable,
    containing a space separated list of Module.symvers files. 

    Within scons, it would be optimal if the the Module.symvers from one module would be a dependency
    for the other modules that use its exported symbols.

    Or we could build all the modules from one Makefile or Kbuild, but that would prevent scons from
    choosing what to build.
"""

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

def generate(env, **kw):

    # Get KERNELDIR from kw dictionary argument that is passed 
    # with the following syntax:
    #   env.Clone(tools=[('kmake',{'KERNELDIR': '/my/kernel/dir'})])

    # If KERNELDIR is not defined or is '*', then an attempt will be
    # made to find the location of the kernel development tree on the
    # current system. The kernel tree is typically provided by the
    # "kernel-devel" package. This tool will try to find the tree
    # using the uname command and the usual path conventions used
    # by RedHat.

    # The above syntax is necessary if this generate is expected to
    # change the value of KERNELDIR. If instead one does:
    #   env.Clone(tools=['kmake'],KERNELDIR='*')
    # then KERNELDIR gets reset back to '*' after this generate is called.

    if kw.has_key('KERNELDIR'):
        env['KERNELDIR'] = kw.get('KERNELDIR')

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
	# Debian
        if not os.path.exists(kdir):
		kdir = '/usr/src/linux-headers-' + krel
        if not os.path.exists(kdir):
            kmach = Popen(['uname','-m'],stdout=PIPE).communicate()[0].rstrip("\n")
            kdir = '/usr/src/kernels/' + krel + '-' + kmach
            if not os.path.exists(kdir):
                # Remove PAE or xen from uname -r output
                krel = krel.replace("xen","")
                krel = krel.replace("PAE","")
                kdir = '/usr/src/kernels/' + krel + '-' + kmach

        env.Replace(KERNELDIR = kdir)

    print 'kmake: KERNELDIR=' + env['KERNELDIR']

    if not env.has_key('KCFLAGS'):
        env['KCFLAGS'] = '-I' + env.Dir("#").get_abspath()

    if not env.has_key('KMAKE'):
        env['KMAKE'] = "make KERNELDIR=$KERNELDIR KCFLAGS=\"$KCFLAGS\""

    k = env.Builder(action=Kmake,
                    source_scanner=SCons.Tool.SourceFileScanner)
    env.Append(BUILDERS = {'Kmake':k})

def exists(env):
    # In scons v2.1.0, and probably all versions before that, this method is
    # not executed when the tool is loaded, but its existence is detected,
    # in order for kmake to recognized as a tool. Just in case it might be
    # executed in a future version of scons, tools make an attempt to check
    # whether they might succeed. Return the existence of make and CC.
    return bool(env.Detect('make')) and bool(env.Detect(env['CC']))
