import os
from eol_scons.package import Package

actions = [
    "./configure --prefix=$OPT_PREFIX",
    "make all",
    "make install"
    ]

installs = [ "$OPT_PREFIX/lib/libudunits.a", "$OPT_PREFIX/include/udunits.h" ]

class UdunitsPackage(Package):

    def __init__(self):
        Package.__init__(self, "UDUNITS", "src/configure",
                         actions, installs,
                         default_package_file = 'udunits-1.12.4.tar.Z')

    def require(self, env):
        env.AppendUnique(CPPPATH=os.path.join(env['OPT_PREFIX'],'include'))
        targets = self.checkBuild(env)
        if self.building:
            env.Append(LIBS=targets[0])
        else:
            env.Append(LIBS='udunits')
            env.Append(LIBPATH=os.path.join(env['OPT_PREFIX'],'lib'))

udunits = UdunitsPackage()

def generate(env):
    udunits.require(env)




def exists(env):
    return True

