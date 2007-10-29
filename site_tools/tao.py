import os
import SCons

def tao_idl_emitter(target, source, env):
    if len(source) == 0:
        print 'no source file'
        return [], []
    # print "emitting idl targets for source ", str(source[0])
    name, ext = SCons.Util.splitext(str(source[0]))
    targets = []
    targets.append ("%sS.cpp" % (name))
#    targets.append ("%sC.cpp" % (name))
#    targets.append ("%sS_T.cpp" % (name))
    targets.append ("%sS.h" % (name))
    targets.append ("%sC.h" % (name))
    targets.append ("%sS_i.h" % (name))
    targets.append ("%sC_i.h" % (name))
    targets.append ("%sS_T_i.h" % (name))
    targets.append ("%sS_T.h" % (name))
    env.SideEffect ("%sC.cpp" % (name), targets[0])
    env.SideEffect ("%sS_T.cpp" % (name), targets[0])
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
    env['TAO_IDL'] = os.path.join("$TAO_ROOT","TAO_IDL","tao_idl")
    env['TAO_IDL_FLAGS'] = '-si S_i.h -st S_T_i.h -ci C_i.h -o $SOURCE.dir'
    env['TAO_IDL_COM'] = '$TAO_IDL $TAO_IDL_FLAGS $SOURCE'
    env.AppendENVPath ('LD_LIBRARY_PATH',
                       os.path.join(env['ACE_ROOT'], 'lib'))
    #env.AppendENVPath ('LD_LIBRARY_PATH',
    #                   os.path.join(os.environ['QTDIR'], 'lib'))

mykey="HAS_PKG_TAO"

def generate(env):
    env.Require(['ace', 'doxygen'])
    if not env.has_key(mykey):
        tao_root=os.path.join(env['ACE_ROOT'],'TAO')
        env['TAO_ROOT'] = tao_root
        # TAO tools (like tao_idl) need TAO_ROOT set in their environment too
        env['ENV']['TAO_ROOT'] = tao_root
        env.Append(CPPPATH=[ tao_root, os.path.join(tao_root,"orbsvcs") ])
        env.AppendDoxref("tao:%s/html/tao" % (env['ACE_ROOT']))
        tao_idl_generate(env)

    env.Append(LIBS=['TAO',])
    env[mykey] = 1


def exists(env):
    return True

