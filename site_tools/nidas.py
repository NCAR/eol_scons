import os
import eol_scons
from SCons.Variables import EnumVariable
import SCons.Warnings

class NidasPathNotDirectory(SCons.Warnings.Warning):
    pass

_options = None

_warned_paths = {}

def generate(env):
    global _options
    if not _options:
        _options = env.GlobalVariables()
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
        for p in paths:
            np = env.Dir("#").Dir(env.subst(p)).get_abspath()
            if not os.path.isdir(np):
                if not _warned_paths.has_key(np):
                    print "NIDAS path is not a directory: " + np
                _warned_paths[np] = 1
            else:
                nidas_paths.append(np)
        if len(nidas_paths) == 0:
            raise NidasPathNotDirectory(
                "No directories found in NIDAS_PATH: %s; " % \
                    env['NIDAS_PATH'] + "disable NIDAS with NIDAS_PATH=''")
        env.EnableNIDAS = (lambda: 1)
    if env.EnableNIDAS():
        env.Append(CPPPATH=[os.path.join(p,'x86','include') 
                            for p in nidas_paths])
        env.Append(LIBPATH=[os.path.join(p,'x86','lib') for p in nidas_paths])
        # The nidas library contains nidas_util already, so only the nidas
        # and nidas_dynld libraries need to be linked.  Linking nidas_util
        # causes static constructors to run multiple times (and
        # subsequently multiple deletes).
        nidas_libs = ['nidas','nidas_dynld','nidas_util']
        env.Append(LIBS=nidas_libs)
        env.AppendUnique(DEPLOY_SHARED_LIBS=nidas_libs)
        env.AppendUnique(RPATH=[os.path.join(p,'x86','lib') 
                                for p in nidas_paths])
        # env.Tool("xercesc")

def exists(env):
    return True
