import os

gccdir = '/opt/local/m68k-wrs-vxworks'

def generate(env):
    env['GCCDIR'] = gccdir
    bindir = gccdir + '/bin'
    env.PrependENVPath ('PATH', bindir)
    env['CC'] = 'm68k-wrs-vxworks-gcc'
    env['LD'] = 'm68k-wrs-vxworks-ld'
    env['AS'] = 'm68k-wrs-vxworks-as'
    env['AR'] = 'm68k-wrs-vxworks-ar'
    env['CXX'] = 'm68k-wrs-vxworks-g++'
    env['RANLIB'] = 'm68k-wrs-vxworks-ranlib'
    env['CCFLAGS'] = ['-fno-builtin', '-w']
    # The ld "Build global constructor/destructor tables" flag (-Ur) is 
    # absolutely required for VxWorks. The -S and -X flags to ld just give us
    # a smaller final product by removing some unnecessary symbols.
    env.AppendUnique(LINKFLAGS = ['-Wl,-Ur', '-Wl,-S', '-Wl,-X'])
    libgcc = os.popen(env.subst('$GCCDIR/bin/$CXX -print-file-name=libgcc.a')).read()
    libcxx = os.popen(env.subst('$GCCDIR/bin/$CXX -print-file-name=libstdc++.a')).read()
    env['LIBGCC'] = libgcc.strip()
    env['LIBSTDCXX'] = libcxx.strip()

def exists(env):
    testenv = env.Clone()
    testenv.PrependENVPath('PATH', gccdir + '/bin')
    print 'checking for m68k-wrs-vxworks-gcc'
    return testenv.Detect('m68k-wrs-vxworks-gcc')
