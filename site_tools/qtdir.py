# -*- python -*-

from eol_scons import parseconfig
from SCons.Options import PathOption

# Set a default for the QTDIR option one time and apply the option value to
# each environment which requires this module.  If the QTDIR environment
# variable is set, then that value is the default.  Otherwise, look for a
# qt directory in /usr/lib.

options = None

def generate(env):
  global options
  if not options:
    options = env.GlobalOptions()
    qt_root = parseconfig.PkgConfigPrefix(env, 'qt-mt', None)
    # Resort to the past method if pkg-config not available:
    if not qt_root:
      qt_root = env.FindPackagePath('QTDIR','/usr/lib/qt-*','/usr/lib/qt-3.3')
    options.AddOptions (PathOption('QTDIR', 'Qt prefix directory.', qt_root))
  options.Update(env)

def exists(env):
  return True
