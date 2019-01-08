"""
SCons tool to add a pseudo-builder which will build a program with
setuid root permission.

Externally, SetuidProgram looks like the Program builder, and it uses the
Program builder, but extends Program's actions:
  o assures that the effective UID is 0, i.e., the root user, when building
  o changes the <owner>:<group> for the built program to root:root
  o enables the setuid bit in the program permissions so that it will
    execute as the file's owner

Usage in a SConstruct most commonly looks something like:

    env.Require("SetuidProgram")
    foo = env.SetuidProgram('foo', 'foo.cpp')
    if (GetOption("clean")):
        env.Default(foo)

and a common build will then look something like:

    $ scons             # builds the normal pieces of the project
    $ sudo scons foo    # builds only the setuid root 'foo' program

Note that the example SConstruct does *not* add the setuid 'foo' target to the
default build, since that target can only be built by root. It does, however,
add a default to remove the target when cleaning.

The common build is done in two steps, with the default normal build performed
by a non-root user, and the setuid program built separately as an explicit
target by root.
"""

import SCons
import os
import platform
from SCons.Action import Action
from SCons.Errors import StopError

def _setuidFailIfNotRoot(env, target, source):
    """
    Fail with SCons.Errors.StopError if the user attempting to build is not root
    """
    try:
        assert(os.geteuid() == 0)
    except:
        print('You must be root to build setuid program {}'.format(target[0]))
        raise StopError

def SetuidProgram(env, target, source, **kw):
    """
    Pseudo-builder to build a setuid program:
    1) PreAction: validate that the (effective) user is root
    2) use the Program builder to make the target
    3) PostAction: set target's owner/group to root:root and enable the
       setuid bit in permissions
    """
    p = env.Program(target, source, **kw)
    env.AddPreAction(p, Action(_setuidFailIfNotRoot))
    env.AddPostAction(p, Action([ "chown root:root $TARGET",
                                  "chmod 4755 $TARGET" ]))
    return p

def generate(env):
     env.AddMethod(SetuidProgram)

def exists(env):
    # This only works under Linux...
    return(platform.system() == "Linux")
