import os
import eol_scons
from SCons.Options import EnumOption
import SCons.Warnings

class NidasPathNotDirectory(SCons.Warnings.Warning):
    pass

_options = None

def generate(env):
    global _options
    if not _options:
        _options = env.GlobalOptions()
        _options.Add('NIDAS_PATH',
"""Set the NIDAS prefix paths, and enable builds of components
which use NIDAS. Setting it to empty disables NIDAS components.
This can be a comma-separated list of paths, for example to build
against a NIDAS installation whose other dependencies are installed
under another prefix.  Relative paths will be converted to absolute
paths relative to the top directory.""",
                    "/opt/local/nidas")
    _options.Update(env)
    env.EnableNIDAS = (lambda: 0)
    nidas_paths = []
    if env.has_key('NIDAS_PATH') and env['NIDAS_PATH']:
        paths=env['NIDAS_PATH'].split(",")
        env.EnableNIDAS = (lambda: 1)
        for p in paths:
            np = env.Dir("#").Dir(env.subst(p)).get_abspath()
            if not os.path.isdir(np):
                raise NidasPathNotDirectory(
                    "Non-empty NIDAS_PATH is not a directory: %s; " % np +
                    "Disable with NIDAS_PATH=''")
            else:
                nidas_paths.append(np)
    if env.EnableNIDAS():
        env.Append(CPPPATH=[os.path.join(p,'x86','include') 
                            for p in nidas_paths])
        env.Append(LIBPATH=[os.path.join(p,'x86','lib') for p in nidas_paths])
        # The nidas library contains nidas_util already, so only the nidas
        # and nidas_dynld libraries need to be linked.  Linking nidas_util
        # causes static constructors to run multiple times (and
        # subsequently multiple deletes).
        nidas_libs = ['nidas','nidas_dynld','XmlRpc']
        env.Append(LIBS=nidas_libs)
        env.AppendUnique(DEPLOY_SHARED_LIBS=nidas_libs)
        env.AppendUnique(RPATH=[os.path.join(p,'x86','lib') 
                                for p in nidas_paths])
        env.Tool("xercesc")

def exists(env):
    return True
