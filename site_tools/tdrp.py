# Tool which provides a builder to use tdrp_gen to build Params.cc and Params.hh
# from file paramdef.<appname>.
#
# After loading this tool in env, just add:
#
#     env.tdrpParamFiles('foo')
#
# to cause Params.cc and Params.hh to be generated for app 'foo' from
# file paramdef.foo.
import os
from SCons.Builder import Builder

# Modify target and source to their real values. The incoming target should be 
# just be the app name.
# On exit, the source list will be ['paramdef.<appname>'] and the
# target list will be ['Params.cc', 'Params.hh'].
def tdrpModifyTargetAndSource(target, source, env):
    # The *real* source file is 'paramdef.<app_name>'. The app name should be 
    # given as the incoming source.
    source = ['paramdef.' + target[0].name]
    # The *real* targets of this builder are always 'Params.cc' and 'Params.hh'
    target = ['Params.cc', 'Params.hh']
    return target, source

# Assemble the command to build Params.cc and Params.hh files from the 
# specified source file, which should be something like 'paramdef.<appname>'.
# The extension on the source file is assumed to be the app name.
def tdrpGenerator(source, target, env, for_signature):
    # Get the directory of the source file, since we must cd there before
    # running tdrp_gen. We must do this because tdrp_gen explcitly generates
    # Params.cc and Params.hh in the current working directory.
    srcdir = os.path.split(source[0].path)[0]
   
    # The application name is the extension of the source file. I.e.,
    # if the source file is 'paramdef.foo', the application name is 'foo'.
    appname = source[0].name.split('.')[-1]
    return 'cd %s; tdrp_gen -f %s -c++ -prog %s' % (srcdir, source[0].name, appname)

tdrpParamsBuilder = Builder(generator = tdrpGenerator, 
                            emitter = tdrpModifyTargetAndSource)

def generate(env):
    # Add builder 'tdrpParamFiles' to the environment.
    env.Append(BUILDERS = {'tdrpParamFiles' : tdrpParamsBuilder})
    env.Append(LIBS=['tdrp'])

def exists(env):
    return True
