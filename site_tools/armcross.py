"""scons arm tool

Customize an environment to use the GCC ARM cross-compiler tools.
"""

import os
import re
import subprocess
import kmake
import localutils
import SCons.Tool

def generate(env,**kw):
    """
    Add Builders and construction variables for C compilers to an Environment.
    """

    env.Replace(AR	= 'arm-linux-ar')
    env.Replace(AS	= 'arm-linux-as')
    env.Replace(CC	= 'arm-linux-gcc')
    env.Replace(LD	= 'arm-linux-ld')
    env.Replace(CXX	= 'arm-linux-g++')
    env.Replace(LINK	= 'arm-linux-g++')
    env.Replace(RANLIB	= 'arm-linux-ranlib')
    env.Replace(LEX	= 'arm-linux-flex')

    env['KERNELDIR'] = kw.get('KERNELDIR','')

    # If KERNELDIR doesn't exist, issue a warning here and
    # let it fail later.
    if env['KERNELDIR'] != '':
        if os.path.exists(env['KERNELDIR']):
            print 'KERNELDIR=' + env['KERNELDIR'] + ' found'
        else:
            print 'Error: KERNELDIR=' + env['KERNELDIR'] + ' not found. Suggestion: install the kernel-devel or kernel-PAE-devel package, and use KERNELDIR=\'*\'.'

    env['KINCLUDE'] = env.Dir("#").get_abspath()
    env['KMAKE'] = "make KERNELDIR=$KERNELDIR KINCLUDE=$KINCLUDE ARCH=arm CROSS_COMPILE=arm-linux-"

    # temporary hack.  RTLinux vipers have GLIBC_2.3.1
    # and something in nibnidas needs GLIBC_2.3.2
    # so build with old tools as long as we have RTLinux vipers
    # env.PrependENVPath('PATH', '/opt/arm_tools/bin')

    # Append /opt/arcom/bin to env['ENV']['PATH'],
    # so that it is the fallback if arm-linux-gcc is
    # not otherwise found in the path.
    # But scons is too smart. If you append /opt/arcom/bin
    # to env['ENV']['PATH'], scons will remove any earlier
    # occurances of /opt/arcom/bin in the PATH, and you may
    # get your second choice for arm-linux-gcc.
    # So, we only append /opt/arcom/bin if "which arm-linux-gcc"
    # fails.

    if not env.Detect(['arm-linux-gcc','arm-linux-g++']):
        env.AppendENVPath('PATH', '/opt/arcom/bin')
        if not exists(env):
            print("*** arm-linux-gcc and arm-linux-g++ not found on path: %s",
                  env['ENV']['PATH'])
            return

    print("Found %s and %s" % 
          (env.WhereIs('arm-linux-gcc'), env.WhereIs('arm-linux-g++')))

    cxxrev = localutils.get_cxxversion(env)
    if cxxrev != None:
        env.Replace(CXXVERSION = cxxrev)

def exists(env):
    return env.Detect(['arm-linux-gcc','arm-linux-g++'])

