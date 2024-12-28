# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
"""
Tool to add Qwt
"""


import platform
import eol_scons.parseconfig as pc


def generate(env):
    qwtpcname = 'qwt'
    if env.get('QT_VERSION') == 6:
      qwtpcname = 'Qt6Qwt6'
    if env.get('QT_VERSION') == 5:
      qwtpcname = 'Qt5Qwt6'

    pcpath = ''
    # This covers osx x86_64.  ARM uses /opt/homebrew, so when we get to that
    # we will update.
    if platform.system() == 'Darwin':
      pcpath = '--with-path=/usr/local/opt/qwt/lib/pkgconfig --with-path=/usr/local/opt/qt/libexec/lib/pkgconfig'
      # I feel we shouldn't need to add this, but pkg-config is not returning it.
      env.AppendUnique(CPPPATH='/usr/local/opt/qwt/lib/qwt.framework/Headers')


    pc.ParseConfig(env, 'pkg-config ' + pcpath + ' --cflags --libs ' + qwtpcname)


def exists(env):
    return True
