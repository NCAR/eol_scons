from __future__ import print_function
import os
from SCons.Script import Builder
# from SCons.Script import Builder,Action,Execute

def MakeSymLink(target,source,env):
    # cmd = env.subst("cd ${TARGET.dir}; ln -sf ${SOURCE.file} ${TARGET.file}",
    #         target=target,source=source)
    # env.Execute(Action(cmd,cmd))

    if not os.path.lexists(target[0].path):
        os.symlink(os.path.basename(source[0].path),target[0].path)
    elif not os.path.exists(target[0].path) or (os.stat(target[0].path).st_ino != os.stat(source[0].path).st_ino):
        # the above check of inodes to detect whether a symbolic link target
        # actually points to the correct source does not really work.
        # The check needs to be in a special env.Decider() for symbolic links.
        # Otherwise SCons generally doesn't recognize that the target
        # doesn't match the source and won't call this builder,
        # so it doesn't even help to always delete the link here.
        print("relinking " + target[0].path)
        os.unlink(target[0].path)
        os.symlink(os.path.basename(source[0].path),target[0].path)

def generate(env):
    """
    Builder for creating a symbolic link pointing to source called target.
    target's link will only contain the file portion of source,
    with the directory portion removed.
    """
    builder = Builder(action=MakeSymLink,single_source=True)
    env.Append(BUILDERS = {"SymLink": builder})

def exists(env):
    return 1
