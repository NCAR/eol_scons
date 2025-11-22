# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
"""
Tool to add Qwt
"""

import eol_scons.parseconfig as pc

_variables = None


def generate(env):
    qwtpcname = 'qwt'
    if env.get('QT_VERSION') == 6:
        qwtpcname = 'Qt6Qwt6'
    if env.get('QT_VERSION') == 5:
        qwtpcname = 'Qt5Qwt6'

    if env['PLATFORM'] == 'darwin':
        qwtPcPath = env['BREW_PREFIX'] + '/opt/qwt/lib/pkgconfig'
        qtPcPath = env['BREW_PREFIX'] + '/opt/qt/libexec/lib/pkgconfig'

        env.PrependENVPath('PKG_CONFIG_PATH', qtPcPath)
        env.PrependENVPath('PKG_CONFIG_PATH', qwtPcPath)
        # I feel we shouldn't need to add this, but pkg-config is not
        # returning it.
        if env.get('QT_VERSION') == 6:
            env.AppendUnique(CPPPATH=env['BREW_PREFIX']+'/opt/qwt/lib/qwt.framework/Headers')
        if env.get('QT_VERSION') == 5:
            env.AppendUnique(CPPPATH=env['BREW_PREFIX']+'/opt/qwt-qt5/lib/qwt.framework/Headers')

    # on redhat9 qwt-qt6 currently still needs to be built from source, so add
    # ability to set path to pkgconfig file for it
    global _variables
    if not _variables:
        _variables = env.GlobalVariables()
        _variables.Add('QWT_PKG_CONFIG_PATH', 'Path to qwt pkg-config files')
    _variables.Update(env)

    if env.get('QWT_PKG_CONFIG_PATH'):
        env.PrependENVPath('PKG_CONFIG_PATH', env['QWT_PKG_CONFIG_PATH'])

    pc.ParseConfig(env, 'pkg-config --cflags --libs ' + qwtpcname)


def exists(env):
    return True
