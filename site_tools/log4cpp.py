
import os
import string
from eol_scons.package import Package

# Since our log4cpp package is based on a cvs checkout, autogen.sh needs
# to run before running configure.
actions = [
    "./autogen.sh",
    "./configure --with-pthreads --prefix=$OPT_PREFIX",
    "make",
    "make install"
    ]

install_targets = [ "$OPT_PREFIX/lib/liblog4cpp.a",
                    "$OPT_PREFIX/include/log4cpp/Category.hh" ]

class Log4cppPackage(Package):

    def __init__(self):

        Package.__init__(self, "LOG4CPP", "config.status",
                         actions, install_targets,
                         default_package_file = "log4cpp-2005-10-21.tar.gz")
                         
    def require(self, env):
        
        self.checkBuild(env)
        prefix = env['OPT_PREFIX']
        version = '0.3.4b'
        if self.building:
            env.Append(LIBS=env.File(install_targets[0]))
        else:
            env.Append(LIBS=["log4cpp"])
            env.Append(LIBPATH=[prefix])

        env.AppendUnique(CPPPATH=[os.path.join(prefix,'include'),])
        env.AppendUnique(CCFLAGS=["-DLOG4CPP_FIX_ERROR_COLLISION", ])
        env.Append(DEPLOY_SHARED_LIBS='log4cpp')
        if not env.has_key('LOG4CPP_DOXDIR'):
            env['LOG4CPP_DOXDIR'] = "%s/doc/log4cpp-%s/api" % \
                                        (prefix, version)
        if not env.has_key('LOG4CPP_DOXREF'):
            env['LOG4CPP_DOXREF'] = "log4cpp:%s" % env['LOG4CPP_DOXDIR']
        env.AppendDoxref(env['LOG4CPP_DOXREF'])


log4cpp = Log4cppPackage()

def generate(env):
    log4cpp.require(env)

def exists(env):
    return True

