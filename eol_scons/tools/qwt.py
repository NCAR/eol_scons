# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
"""
Tool to add Qwt
"""


import subprocess
import eol_scons.parseconfig as pc


def generate(env):
    qwtpcname = 'qwt'
    if env.get('QT_VERSION') == 6:
      qwtpcname = 'Qt6Qwt6'
    if env.get('QT_VERSION') == 5:
      qwtpcname = 'Qt5Qwt6'

    if env['PLATFORM'] == 'darwin':
      brewPath = subprocess.run(['brew', '--prefix'], capture_output=True, text=True).stdout.strip()
      qwtPcPath = brewPath + '/opt/qwt/lib/pkgconfig'
      qtPcPath = brewPath + '/opt/qt/libexec/lib/pkgconfig'

      env.PrependENVPath('PKG_CONFIG_PATH', qtPcPath)
      env.PrependENVPath('PKG_CONFIG_PATH', qwtPcPath)
      # I feel we shouldn't need to add this, but pkg-config is not returning it.
      env.AppendUnique(CPPPATH=brewPath+'/opt/qwt/lib/qwt.framework/Headers')


    pc.ParseConfig(env, 'pkg-config --cflags --libs ' + qwtpcname)


def exists(env):
    return True
