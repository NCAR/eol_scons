import os

def generate(env):
    # gccdir = "/net/local_lnx/lib/gcc-lib/m68k-wrs-vxworks/2.95.2"
    gccdir = "/opt/local/m68k-wrs-vxworks"
    env['GCCDIR'] = gccdir
    # env.PrependENVPath ('PATH', "/net/local_lnx/bin")
    env.PrependENVPath ('PATH', gccdir+"/bin")
    env['CC'] = 'm68k-wrs-vxworks-gcc'
    env['LD'] = 'm68k-wrs-vxworks-ld'
    env['AS'] = 'm68k-wrs-vxworks-as'
    env['AR'] = 'm68k-wrs-vxworks-ar'
    env['CXX'] = 'm68k-wrs-vxworks-g++'
    env['RANLIB'] = 'm68k-wrs-vxworks-ranlib'
    #env['CCFLAGS'] = ["-fno-builtin", "-nostdinc", "-w"]
    env['CCFLAGS'] = ["-fno-builtin", "-w"]
    bindir=gccdir+"/bin"
    libgcc = os.popen(env.subst("$GCCDIR/bin/$CXX -print-file-name=libgcc.a")).read()
    libcxx = os.popen(env.subst("$GCCDIR/bin/$CXX -print-file-name=libstdc++.a")).read()
    env['LIBGCC'] = libgcc.strip()
    env['LIBSTDCXX'] = libcxx.strip()

def exists(env):
    print "checking for m68k-wrs-vxworks-gcc"
    return env.Detect('m68k-wrs-vxworks-gcc')
