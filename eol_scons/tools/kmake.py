# -*- python -*-
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
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
import fnmatch
import subprocess
import string
import SCons.Errors
import SCons

from subprocess import Popen,PIPE

_default_kerneldir = None

# Set to 1 to enable debugging output
_debug = 0

# Debugging print
def pdebug(msg):
    if _debug: print(msg)

def Kmake(env,target,source):

    if 'KERNELDIR' not in env:
        print("KERNELDIR not specified, %s will not be built" %
              (target[0].abspath))
        return None

    # KERNELDIR is an overloaded scons variable.  It is a user-specified
    # configuration variable, but then it is replaced if it has the special
    # value '*'.  Because variables can be updated anywhere, there is
    # nothing to ensure that the variable is not reset to the default or to
    # whatever the config file specifies, which means the generated default
    # kernel dir can be reset at any time back to '*'.  So catch this
    # situation and apply the default here.  The other way to handle this
    # is to change the default value for the KERNELDIR variable to
    # $KERNELDIR_FOUND, now that the generate() function of this tool sets
    # KERNELDIR_FOUND appropriately, and then KERNELDIR will be rendered
    # correctly on the command line.  For now, this should allow all the
    # existing uses of KERNELDIR to keep working as before.

    if env['KERNELDIR'] == '*':
        env['KERNELDIR'] = '$KERNELDIR_FOUND'
        print("replaced KERNELDIR=* with KERNELDIR=%s" % (env['KERNELDIR']))

    if not os.path.exists(env.subst(env['KERNELDIR'])):
        msg = ('Error: KERNELDIR=' + env.subst(env['KERNELDIR']) +
                ' not found.')
        print(msg)
        raise SCons.Errors.StopError(msg)

    # Have the shell subprocess do a cd to the source directory.
    # If scons/python does it, then the -j multithreaded option doesn't work.
    srcdir = os.path.dirname(source[0].abspath)

    # Grab the Module.symvers sources, put them in a KBUILD_EXTRA_SYMBOLS
    # make option
    symvers = []
    for s in source:
        spath = os.path.basename(s.path) 
        if spath == 'Module.symvers':
            symvers += [s.abspath]
        elif spath == 'Makefile':
            srcdir = os.path.dirname(s.abspath)

    symopt = ''
    if len(symvers) > 0:
        symopt = ' KBUILD_EXTRA_SYMBOLS="' + ' '.join(symvers) + '"'

    return env.Execute('cd ' + srcdir + '; ' + env['KMAKE'] + symopt)

def kemitter(target, source, env):
    return ([target, 'Module.symvers'], source)

def _get_output(cmd):
    "Get command output or stderr if it fails"
    pdebug("kerneldir: running '%s'" % (" ".join(cmd)))
    child = Popen(cmd, stdout=PIPE, stderr=PIPE)
    output = child.communicate()
    sout = output[0].decode().strip()
    eout = output[1].decode().strip()
    pdebug("%s output: %s" % (" ".join(cmd),sout))
    pdebug("%s error: %s" % (" ".join(cmd),eout))
    pdebug("%s returncode: %d" % (" ".join(cmd), child.returncode))
    if child.returncode != 0:
        raise RuntimeError(" ".join(cmd) + ": " + eout)
    return sout

def _GetOSId():
    "Read /etc/os-release to find value of ID"
    try:
        out = _get_output(["sh","-c",". /etc/os-release; echo $ID"])
    except Exception as error:
        msg = "Cannot determine OS ID: %s" % (error)
        raise SCons.Errors.StopError(msg)
    return out

def _GetKernelDir():
    """
    Return the default kernel directory on this system.
    """

    # Settings of KERNELDIR:
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
    # armel debian systems, with custom kernels
    #   /usr/src/linux-headers-3.16.0-titan2 
    #   /usr/src/linux-headers-3.16.0-viper2 
    # VortexDX3, ubuntu
    #   uname -r: 4.6.6
    #   uname -m: i686
    #   factory installation:
    #       /usr/src/linux-headers-4.4.6
    #   working versions from linux-headers packages:
    #       /usr/src/linux-headers-x.y.z-n-generic
    #       eg: /usr/src/linux-headers-4.4.0-190-generic
    #   The linux-headers-x.y.z package also installs
    #       /usr/src/linux-headers-x.y.z-n
    #       but one can't build modules from that tree, you get

    # The default kernel directory should always be the same, so no need to
    # generate it more than once.
    global _default_kerneldir
    if _default_kerneldir:
        return _default_kerneldir

    osid = _GetOSId()
    pdebug("osid=%s" % (osid))

    # A kernel header directory must contain some autoconf files, otherwise
    # you'll get this error when building the modules:
    #   ERROR: Kernel configuration is invalid.
    #         include/generated/autoconf.h or include/config/auto.conf are missing.
    #   WARNING: Symbol version dump ./Module.symvers
    #       is missing; modules will have no dependencies and modversions.
    autoconf = "include/generated/autoconf.h"

    # When building in a docker container, uname gives the version of the host
    # kernel, which is likely not the kernel you're building for.
    # So search for directories of the kernel headers, using the path
    # convention of the OS ID found in /etc/os-release.
    # There doesn't seem to be a foolproof way to determine if you're running
    # in a container for all versions of docker or lxc

    kdir = ''

    if osid == "ubuntu"  or osid == "debian":
        srcdir = "/usr/src"
        dmatch = "linux-headers-*"
        dirs = [d for d in os.listdir(srcdir)
            if os.path.isdir(os.path.join(srcdir,d)) and
                fnmatch.fnmatch(d,dmatch) and
                os.path.isfile(os.path.join(srcdir,d,autoconf))]
        pdebug("KERNELDIRs matching %s: %s" %
            (os.path.join(srcdir,dmatch),",".join(dirs)))

        if len(dirs) > 0:
            kdir = os.path.join(srcdir,dirs[0])
        if len(dirs) > 1:
            print("Warning: %d KERNELDIRs found: %s"
                % (len(dirs), ", ".join(dirs)))
            print("Arbitrarily choosing the first one: %s" % (kdir))

    else:       # if not ubuntu or debian assume RedHat:  centos, fedora
        srcdir = "/usr/src/kernels"
        dirs = [d for d in os.listdir(srcdir)
            if os.path.isdir(os.path.join(srcdir,d)) and
                os.path.isfile(os.path.join(srcdir,d,autoconf))]
        pdebug("KERNELDIRs in %s: %s" % (srcdir,",".join(dirs)))

        if len(dirs) > 1:
            print("Warning: %d KERNELDIRs found: %s"
                % (len(dirs), ", ".join(dirs)))
            # On RedHat, assume we're not in a container and use "uname -r" to
            # match the KERNELDIR
            krel = _get_output(['uname','-r'])
            pdebug("Looking for match with $(uname -r): %s" % krel)
            udirs = [d for d in dirs if fnmatch.fnmatch(d,krel + '*')]
            if len(udirs) > 0:
                dirs = udirs
        if len(dirs) > 0:
            kdir = os.path.join(srcdir,dirs[0])
        if len(dirs) > 1:
            print("Warning: %d KERNELDIRs found: %s"
                % (len(dirs), ", ".join(dirs)))
            print("Arbitrarily choosing the first one: %s" % (kdir))

    _default_kerneldir = kdir
    return kdir

def generate(env, **kw):

    # Get KERNELDIR from kw dictionary argument that is passed 
    # with the following syntax:
    #   env.Clone(tools=[('kmake',{'KERNELDIR': '/my/kernel/dir'})])

    # If KERNELDIR is not defined or is '*', then an attempt will be
    # made to find the location of the kernel development tree on the
    # current system.

    # The above syntax is necessary if this generate is expected to
    # change the value of KERNELDIR. If instead one does:
    #   env.Clone(tools=['kmake'],KERNELDIR='*')
    # then KERNELDIR gets reset back to '*' after this generate is called.

    env.AddMethod(_GetKernelDir, "GetKernelDir")
    env.AddMethod(_GetOSId, "GetOSId")

    if 'KERNELDIR' in kw:
        env['KERNELDIR'] = kw.get('KERNELDIR')

    kdir = _GetKernelDir()
    env.Replace(KERNELDIR_FOUND = kdir)
    print("setting KERNELDIR_FOUND=%s" % (kdir))

    if 'KERNELDIR' not in env or env['KERNELDIR'] == '*':
        env.Replace(KERNELDIR = kdir)

    print('kmake: KERNELDIR=' + env['KERNELDIR'])

    if 'KCFLAGS' not in env:
        env['KCFLAGS'] = '-I' + env.Dir("#").get_abspath()

    if 'KMAKE' not in env:
        env['KMAKE'] = 'make KERNELDIR=$KERNELDIR KCFLAGS="$KCFLAGS"'

    k = env.Builder(action=Kmake,
                    emitter=kemitter,
                    source_scanner=SCons.Tool.SourceFileScanner)
    env.Append(BUILDERS = {'Kmake':k})

def exists(env):
    # In scons v2.1.0, and probably all versions before that, this method is
    # not executed when the tool is loaded, but its existence is detected,
    # in order for kmake to recognized as a tool. Just in case it might be
    # executed in a future version of scons, tools make an attempt to check
    # whether they might succeed. Return the existence of make and CC.
    return bool(env.Detect('make')) and bool(env.Detect(env['CC']))
