# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
import os
import SCons
import sys


class ToolOsxDmgAppWarning(SCons.Warnings.WarningOnByDefault):
    pass


class NotAnOsxSystem(ToolOsxDmgAppWarning):
    pass


def create_dmg(target, source, env):
    sources = source
    if not isinstance(sources, list):
        sources = [source]

    # The disk image name is the first target.
    dmg = str(target[0])

    # make sure that it has a .dmg extension
    x = dmg.replace('.dmg', '')
    if dmg == x:
        # No .dmg found, so append it
        dmg = dmg + '.dmg'

    # remove an existing dmg
    os.system('rm -rf %s' % dmg)

    # Create the volume name from the disk image name
    volname = str(target[0]).replace('.dmg', '')
    volname = os.path.basename(volname)

    # Create the srcfolder switches for hdiutil
    srcfolders = ''
    for f in sources:
        srcfolders = ' -srcfolder ' + str(f)

    # Create the disk image using hdiutil
    os.system('hdiutil create ' + srcfolders + ' -volname %s %s' %
              (volname, dmg))


def create_dmg_message(target, source, env):
    return "Creating disk image " + str(target[0])


def generate(env):
    """
    Add a builder for OsxDmg

    The target is the name of the disk image to be created. It may or may
    not contain the .dmg extension.

    The source(s) are the directories which will be included in the disk
    image.
    """
    bldr = env.Builder(action=env.Action(create_dmg, create_dmg_message))
    env.Append(BUILDERS={'OsxDmg': bldr})


def exists(env):
    if sys.platform != 'darwin':
        raise SCons.Errors.StopError(
            NotAnOsxSystem,
            "Trying to create a disk image on a non-OSX system")
    return True
