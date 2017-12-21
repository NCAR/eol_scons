"""
Builders to unpack archive packages.
"""

import os
import SCons
import string
import new

unpack_variables=[]

def unpack_emitter(target, source, env):

    pass

# The technique of passing this dictionary as the action to create a
# Builder doesn't work because scons looks for .Z and does not see .tar.Z.
# Instead this dictionary is used in the action generator.

suffix_actions = {
    ".tar.gz" : "tar zxf $SOURCE",
    ".tar.Z" : "tar zxf $SOURCE",
    ".zip" : "unzip -q -o $SOURCE"
}

suffixes = list(suffix_actions.keys())

def getPackageName(env, filepath):
    filename = os.path.basename(filepath)
    for k in suffixes:
        if filename.endswith(k):
            return filename[0:string.rfind(filename,k)]
    return filename

def unpack_generator(target, source, env, for_signature):
    """Given a source package, try to parse the extension to determine
       how to unpack it."""
    
    filename = str(source[0])
    for k in suffixes:
        if filename.endswith(k):
            return suffix_actions[k]

    return None

unpack_builder = SCons.Builder.Builder( generator = unpack_generator,
                                        single_source = 1,
                                        src_suffix = suffixes )

def generate(env):
    """Add builders and construction variables for unpacking tools."""
    env['BUILDERS']['Unpack'] = unpack_builder
    env.getPackageName = new.instancemethod(getPackageName,env,env.__class__)


if 0:

    udunits = "/net/ftp/pub/archive/aeros/packages/udunits-1.12.4.tar.Z"
    qwt = "/net/ftp/pub/archive/aeros/packages/qwt-4.2.0.zip"
    netcdf = "/net/ftp/pub/archive/aeros/packages/netcdf-3.6.0-p1.tar.gz"

    env = Environment()
    generate(env)

    print(env.getPackageName(udunits))
    print(env.getPackageName(qwt))
    print(env.getPackageName(netcdf))

    env.Default(env.Unpack(target="qwt-4.2.0/INSTALL", source=qwt))
    env.Default(env.Unpack(target="udunits-1.12.4/src/INSTALL",
                           source=udunits))
    env.Default(env.Unpack(target="netcdf-3.6.0-p1/src/INSTALL",
                           source=netcdf))


def exists(env):
    return True

