import os
import eol_scons
from SCons.Options import EnumOption
import SCons.Warnings

class NidasPathNotDirectory(SCons.Warnings.Warning):
    pass

options = None

def generate(env):
    global options
    if not options:
        options = env.GlobalOptions()
        options.Add('NIDAS_PATH',
"""Set the NIDAS install path, and enable builds of components
 which use NIDAS. Setting it to empty disables NIDAS components.""",
                    "/opt/local/nidas")
    options.Update(env)
    if env.has_key('NIDAS_PATH') and env['NIDAS_PATH']:
        np = env['NIDAS_PATH']
        if os.path.isdir(np):
            env.EnableNIDAS = (lambda: 1)
        else:
            env.EnableNIDAS = (lambda: 0)
            raise NidasPathNotDirectory(
                "Non-empty NIDAS_PATH is not a directory: %s; " % np +
                "Disable with NIDAS_PATH=''")
    else:
        env.EnableNIDAS = (lambda: 0)
    if env.EnableNIDAS():
        env.Append(CPPPATH= ['$NIDAS_PATH/x86/include',])
        env.Append(LIBPATH=['$NIDAS_PATH/x86/lib',])
        env.Append(LIBS=['nidas','nidas_dynld','nidas_util','XmlRpc'])
        env.AppendUnique(RPATH="$NIDAS_PATH/x86/lib") 
        env.Tool("xercesc")

def exists(env):
    return True
