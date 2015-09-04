"""scons arm tool

Customize an environment to use the GCC ARM cross-compiler tools.
"""

import eol_scons.utils

def generate(env,**kw):
    """
    Add construction variables for C compilers to an Environment.
    """

    env.Replace(AR	= 'arm-linux-ar')
    env.Replace(AS	= 'arm-linux-as')
    env.Replace(CC	= 'arm-linux-gcc')
    env.Replace(LD	= 'arm-linux-ld')
    env.Replace(CXX	= 'arm-linux-g++')
    env.Replace(LINK	= 'arm-linux-g++')
    env.Replace(RANLIB	= 'arm-linux-ranlib')
    env.Replace(LEX	= 'arm-linux-flex')
    env.Replace(KMAKE   = 'make KERNELDIR=$KERNELDIR KCFLAGS="$KCFLAGS" ARCH=arm CROSS_COMPILE=arm-linux-')

    # Append /opt/arcom/bin to env['ENV']['PATH'],
    # so that it is the fallback if arm-linux-gcc is
    # not otherwise found in the path.
    # But scons is too smart. If you append /opt/arcom/bin
    # to env['ENV']['PATH'], scons will remove any earlier
    # occurances of /opt/arcom/bin in the PATH, and you may
    # get your second choice for arm-linux-gcc.
    # So, we only append /opt/arcom/bin if "which arm-linux-gcc"
    # fails.

    if not exists(env):
        env.AppendENVPath('PATH', '/opt/arcom/bin')
        if not exists(env):
            print("*** arm-linux-gcc and arm-linux-g++ not found on path: %s",
                  env['ENV']['PATH'])
            return

    print("armcross: found %s and %s" % 
          (env.WhereIs('arm-linux-gcc'), env.WhereIs('arm-linux-g++')))

    cxxrev = eol_scons.utils.get_cxxversion(env)
    if cxxrev != None:
        env.Replace(CXXVERSION = cxxrev)

def exists(env):
    return bool(env.Detect('arm-linux-gcc')) and bool(env.Detect('arm-linux-g++'))

