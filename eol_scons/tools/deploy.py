import os
import SCons
from SCons.Builder import Builder
from SCons.Action import Action

from eol_scons.ldd import ldd

# As of scons 1.2 the Mkdir action works even if the directory exists.
# Until everyone is using that, we need to use our own action.
# from SCons.Defaults import Mkdir
from eol_scons.chdir import MkdirIfMissing
Mkdir = MkdirIfMissing


def makedirs(dirpath):
    try:
        print(("mkdir ", dirpath))
        os.makedirs(dirpath)
    except OSError:
        if not os.access(dirpath, os.W_OK):
            raise


def deploy_program_emitter(target, source, env):
    "Given a source program, calculate the targets."
    # We don't know the dependencies until the program has been linked,
    # thus we can't use an emitter to calculate the targets that will
    # be copied into the deploy directory.  So the only target we can
    # generate now is the copy of the program itself.
    bindir = os.path.join(env['DEPLOY_DIRECTORY'], env['DEPLOY_BINDIR'])
    dest = os.path.join(bindir, source[0].name)
    # The target depends on the setting of DEPLOY_SHARED_LIBS, even though
    # that variable is not referenced anywhere scons can detect it.  So add
    # it as an explicit dependency node.
    libslist = env.Value(",".join(env['DEPLOY_SHARED_LIBS']))
    target = [dest]
    source = source+[libslist]
    env.LogDebug("deploy_program_emitter()->%s, %s" %
                 ([str(t) for t in target], [str(s) for s in source]))
    return target, source


def deploy_program(target, source, env):
    """
    Copy a program target into a deploy tree along with all of its dynamic
    dependencies.
    """
    # Resolve any # notation in the deploy directory setting before using
    # it.  The str() is in case the setting is a scons node and not a
    # string.
    dpath = env.Dir(str(env['DEPLOY_DIRECTORY'])).get_path()
    bindir = os.path.join(dpath, env['DEPLOY_BINDIR'])
    libdir = os.path.join(dpath, "lib")
    actions = [Mkdir(bindir), Mkdir(libdir)]
    progdest = target[0]
    libraries = ldd(source[0], env, env['DEPLOY_SHARED_LIBS'])
    cp = 'cp -fp'
    actions.append(f'{cp} "{source[0]}" "{progdest}"')
    for k in libraries:
        libfile = libraries[k]
        libdest = os.path.join(libdir, libfile.name)
        # Use an explicit cp command rather than Copy. Both the Copy() API
        # and default behavior regarding deep/shallow copies changed in
        # scons v2.3.5. This created a problem when copying symlinked
        # objects such as system dynamic libraries.  This should be portable
        # enough since deploy is not used on Windows.
        actions.append(Action(f'{cp} "{libfile.get_abspath()}" "{libdest}"'))
    return env.Execute(actions)


# Ultimately, DeployProgram probably should be a wrapper which creates
# individual builders for copying all the shared libraries and the program.
# That way all the copied files would be targets which would be erased by a
# scons clean, and they would be copied over if the system library source
# changed.  Oh well, this works for now.

deploy_program_builder = Builder(action=deploy_program,
                                 emitter=deploy_program_emitter)


class DeployWarning(SCons.Errors.UserError):
    pass


def generate(env):
    env.SetDefault(DEPLOY_SHARED_LIBS=[])
    env.SetDefault(DEPLOY_DIRECTORY="#deploy")
    env.SetDefault(DEPLOY_BINDIR="bin")
    env['BUILDERS']['DeployProgram'] = deploy_program_builder


def exists(env):
    return True
