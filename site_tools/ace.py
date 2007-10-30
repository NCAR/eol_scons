
import os
import eol_scons
import string
from SCons.Options import PathOption

options = None

def generate(env):

  env.Require(['doxygen'])
  global options
  if not options:
    options = env.GlobalOptions()
    ace_root=env.FindPackagePath('ACE_ROOT','$OPT_PREFIX/ACE*','/opt/ACE')
    options.AddOptions(PathOption('ACE_ROOT', 'ACE_ROOT directory.', ace_root))
    options.Add('ACE_NTRACE', 'Definition of ACE_NTRACE CPP macro, 0 or 1.', 0)
  options.Update(env)
  # Use the existence of a key in the env to separate the ACE tool into
  # what need only be applied once and what must be applied every time this
  # tool is Require()d by another package.  Basically that means the library
  # must always be appended; everything else happens once.
  #env.AppendUnique(CPPPATH=[ace_root])
  ace_root = env['ACE_ROOT']
  env['ENV']['ACE_ROOT'] = ace_root
  ace_inc='-I%s' % ace_root
  env.AppendUnique(CCFLAGS=[ace_inc])

  if not env.has_key('HAS_PKG_ACE'):
    libpath=os.path.join(ace_root, 'lib')
    env.AppendUnique(LIBPATH=[libpath])
    env.AppendUnique(RPATH=[libpath]) 
    env['ACE_ROOT'] = ace_root
    env['ENV']['ACE_ROOT'] = ace_root
    env.AppendUnique(CPPDEFINES = 
      string.split("""POSIX_THREADS POSIX_THREAD_SAFE_FUNCTIONS REENTRANT AC 
                      ACE_HAS_AIO_CALLS ACE_HAS_EXCEPTIONS ACE_HAS_QT
                      ACE_LACKS_PRAGMA_ONCE"""))  
#    env.Append(CPPDEFINES=['ACE_NTRACE=${ACE_NTRACE}'])
    env.AppendDoxref("ace:%s/html/ace" % (ace_root))
    env['HAS_PKG_ACE'] = 1
  env.Append(LIBS=['ACE',])


def exists(env):
    return True

