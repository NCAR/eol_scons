import os
from SCons.Script import Builder
# from SCons.Script import Builder,Action,Execute

def MakeSymLink(target,source,env):
    # cmd = env.subst("cd ${TARGET.dir}; ln -sf ${SOURCE.file} ${TARGET.file}",
    #         target=target,source=source)
    # env.Execute(Action(cmd,cmd))
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
