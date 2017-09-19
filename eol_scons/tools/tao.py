from __future__ import print_function
import os
import SCons
from SCons.Variables import PathVariable

_options = None
mykey="HAS_PKG_TAO"

def tao_idl_emitter(target, source, env):
    if len(source) == 0:
        print('no source file')
        return [], []
    # print "emitting idl targets for source ", str(source[0])
    name, ext = SCons.Util.splitext(str(source[0]))
    targets = []
    targets.append ("%sS.cpp" % (name))
    # targets.append ("%sC.cpp" % (name))
    # targets.append ("%sS_T.cpp" % (name))
    targets.append ("%sS.h" % (name))
    targets.append ("%sC.h" % (name))
    # targets.append ("%sS_i.h" % (name))
    targets.append ("%sC_i.h" % (name))
    # targets.append ("%sS_T.h" % (name))
    targets.append ("%sC.cpp" % (name))
    # env.SideEffect ("%sS_T.cpp" % (name), targets[0])
    # print "returning targets, source: ", targets, source[0]
    return targets, source

import SCons.Scanner.IDL
idl_scanner = SCons.Scanner.IDL.IDLScan()

tao_idl_builder = SCons.Builder.Builder(action='$TAO_IDL_COM',
                                        src_suffix = '.idl',
                                        suffix='.cpp',
                                        emitter = tao_idl_emitter,
                                        source_scanner = idl_scanner)

def createBuilder(env):

    c_file, cxx_file = SCons.Tool.createCFileBuilders(env)
    cxx_file.add_action('.idl', '$TAO_IDL_COM')
    cxx_file.add_emitter('.idl', tao_idl_emitter)
    return cxx_file

def tao_idl_generate(env):
    """Add builders and construction variables for TAO IDL."""

    # env['BUILDERS']['TaoIDL'] = tao_idl_builder
    createBuilder(env)

    tao_idl_path = os.path.join(env['TAO_ROOT'], "TAO_IDL", "tao_idl")
    env['TAO_IDL'] = tao_idl_path
    env['TAO_IDL_FLAGS'] = '-ci C_i.h -o $SOURCE.dir'
    env['TAO_IDL_COM'] = '$TAO_IDL $TAO_IDL_FLAGS $SOURCE'
    # tao_idl requires LD_LIBRARY_PATH allow for finding ACE/TAO libraries
    env.AppendENVPath('LD_LIBRARY_PATH', os.path.join(env['ACE_ROOT'], 'lib'))

def generate(env):

    # Require ace first, so the TAO_ROOT default can depend on it.
    if mykey not in env:
        env.Require(['ace', 'doxygen'])

    global _options
    if not _options:
        _options = env.GlobalVariables() 
        tao_root = env.FindPackagePath('TAO_ROOT', '$ACE_ROOT/TAO', '/usr')
        _options.AddVariables(PathVariable('TAO_ROOT', 'TAO_ROOT directory.', 
                                       tao_root))
    _options.Update(env)

    # Use the existence of a key in the env to separate the TAO tool
    # into what need only be applied once and what must be applied
    # every time this tool is Require()d by another package.
    # Basically that means the library must always be appended;
    # everything else happens once.
    if mykey not in env:
        tao_root = env['TAO_ROOT']
        # TAO tools (like tao_idl) need TAO_ROOT set in their environment too
        env['ENV']['TAO_ROOT'] = tao_root
        # add TAO_ROOT and TAO_ROOT/orbsvcs to the include path
        env.Append(CPPPATH=[tao_root, os.path.join(tao_root, "orbsvcs")])
        env.SetDefault(TAO_DOXREF="tao:$ACE_ROOT/html/tao")
        env.AppendDoxref("$TAO_DOXREF")
        tao_idl_generate(env)
        env[mykey] = 1

    env.Append(LIBS=['TAO',])


def exists(env):
    return True
