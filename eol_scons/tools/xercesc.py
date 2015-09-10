# -*- mode: python; -*-

import os
from SCons.Script import BoolVariable

_options = None

def generate(env):

    prefix = None
    global _options
    if not _options:
        _options = env.GlobalVariables()
        _options.Add(
            BoolVariable('xercesc27',
                         """
Enable special paths for xerces 2.7 compatibility on Fedora.
Requires the xerces-c27-devel package to be installed.""",
                         False))
    _options.Update(env)
    x27 = env['xercesc27']
    if env.has_key('XERCESC_PREFIX'):
        prefix = env.subst(env['XERCESC_PREFIX'])
    elif env.has_key('OPT_PREFIX') and not x27:
        prefix = env.subst(env['OPT_PREFIX'])
        env['XERCESC_PREFIX'] = prefix
    env.Append(LIBS=['xerces-c'])
    if bool(prefix and
            os.path.exists(os.path.join(prefix,
                                        'lib', 'libxerces-c.so'))):
        env.AppendUnique(LIBPATH=[os.path.join(prefix, 'lib')])
        env.AppendUnique(CPPPATH=[os.path.join(prefix, 'include'),])

    # Supply a hard-coded default for finding doxygen docs
    if not env.has_key('XERCESCROOT'):
        env['XERCESCROOT'] = '/net/src/prog-tools/xerces-c-src_2_6_0'

    if not env.has_key('XERCESC_DOXDIR'):
        env['XERCESC_DOXDIR'] = "%s/doc/html/apiDocs" % env['XERCESCROOT']
    doxref= "xercesc:%s" % env['XERCESC_DOXDIR']
    env.AppendDoxref(doxref)

    # If no prefix was set explicitly, and the 2.7 handling is enabled,
    # then look for special paths for the xerces-c27 package on Fedora.
    if not prefix and x27:
        env.AppendUnique(CPPPATH=['/usr/include/xercesc-2.7.0'])
        if os.path.exists('/usr/lib64/xerces-c-2.7.0'):
            env.AppendUnique(LIBPATH=['/usr/lib64/xerces-c-2.7.0'])
        else:
            env.AppendUnique(LIBPATH=['/usr/lib/xerces-c-2.7.0'])


def exists(env):
    return True

