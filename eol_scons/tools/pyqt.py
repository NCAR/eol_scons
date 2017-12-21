# $Id$
#
import os, os.path

from SCons.Script import Builder

# support for Python QT - generate python files from designer .ui files

def generate(env):
    try:
        qt_root= env['QTDIR']
    except KeyError:
        qt_root= os.environ['QTDIR']
    qt_lib = os.path.join(qt_root,'lib')
    # Fedora Core 2 and 3 have a PyQt RPM with pyuic
    if ((env['DISTRIBUTION'][0:2] == 'fc') or (env['DISTRIBUTION'] == 'el4')):
        pyuic = '/usr/bin/pyuic'
    else:
        # we install pyuic separately for Redhat Enterprise
        pyuic = os.path.join(env['OPT_PREFIX'], 'bin', 'pyuic')
    PYUIC="LD_LIBRARY_PATH=%s %s" % (qt_lib, pyuic)
    # defining this  builder doesn't  put it into the environment?!
    bld = Builder(action='%s -o  $TARGET $SOURCE' % PYUIC, src_suffix='.ui',
                  suffix='.py')
    env['BUILDERS']['PYUIC']= bld

    # we need to propage HOME, to make pyuic stop complaining
    uic = 'HOME="%s" %s' % (os.environ['HOME'], PYUIC)
    env['PY_UIC'] = uic
    

def exists(env):
    return True

