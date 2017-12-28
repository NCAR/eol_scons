from __future__ import print_function
import os
import re
import subprocess
import SCons
from SCons.Builder import Builder
from SCons.Action import Action
import shutil

from SCons.Defaults import Copy

# As of scons 1.2 the Mkdir action works even if the directory exists.
# Until everyone is using that, we need to use our own action.
# from SCons.Defaults import Mkdir
from eol_scons.chdir import MkdirIfMissing
Mkdir = MkdirIfMissing

def makedirs(dirpath):
    try:
        print(("mkdir ", dirpath))
        os.makedirs(dirpath)
    except:
        if not os.access(dirpath, os.W_OK):
            raise


def ldd(program_node, env):
    "Return a map with each dependent library name and its location."
    libraries = {}
    # Run ldd on the program
    lddcmd = ["ldd", program_node.get_abspath()]
    print(lddcmd)
    lddprocess = subprocess.Popen(lddcmd, stdout=subprocess.PIPE)
    lddout = lddprocess.communicate()[0].decode()
    print(lddout)
    # Get the list of library keys to include
    libkeys = env['DEPLOY_SHARED_LIBS']
    # print("Looking for these libraries:\n"+ "\n".join(libkeys))
    for k in libkeys:
        # If the library is in the dependencies, then the file will
        # be copied into the deploy lib directory
        match = re.search(r"lib%s\..*=> (.+) \(" % re.escape(env.subst(k)),
                          lddout, re.MULTILINE)
        if match:
            lib = env.File(match.group(1))
            if lib.name not in libraries:
                print("Found %s" % (str(lib)))
                libraries[lib.name] = lib
                libraries.update (ldd(lib, env))
    return libraries


def deploy_program_emitter(target, source, env):
    "Given a source program, calculate the targets."
    # We don't know the dependencies until the program has been linked,
    # thus we can't use an emitter to calculate the targets that will
    # be copied into the deploy directory.  So the only target we can
    # generate now is the copy of the program itself.
    bindir = os.path.join(env['DEPLOY_DIRECTORY'], "bin")
    dest = os.path.join(bindir, source[0].name)
    return [dest], source


def deploy_program(target, source, env):

    """Copy a program target into a deploy tree along with all of its
    dynamic dependencies."""
    # Resolve any # notation in the deploy directory setting before using
    # it.  The str() is in case the setting is a scons node and not a
    # string.
    dpath = env.Dir(str(env['DEPLOY_DIRECTORY'])).get_path()
    bindir = os.path.join(dpath, "bin")
    libdir = os.path.join(dpath, "lib")
    actions = [ Mkdir(bindir), Mkdir(libdir) ]
    progdest = target[0]
    libraries = ldd(source[0], env)
    actions.append (Copy(progdest, source[0]))
    for k in libraries:
        libfile = libraries[k]
        libdest = os.path.join(libdir, libfile.name)
        # Use an explicit cp command rather than Copy. Both the Copy() API and default 
        # behavior regarding deep/shallow copies changed in scons v2.3.5. This created
        # a problem when copying symlinked objects such as system dynamic libraries.
        actions.append (Action('cp ' + libfile.get_abspath() + ' ' + libdest))
    return env.Execute(actions)


# 2009-09-25 GJG: The parameters for creating a global Action seem to have
# changed.  Instead of taking a list of variables, the variables are passed
# as parameters.  Instead of risking that the new form would break users of
# older scons version, don't pass the variables variables.
#
# Actually, it seems better to generate the list of Mkdir and Copy, so
# scons can execute them and use the default messages and signatures.
# Ultimately, DeployProgram probably should be a wrapper which creates
# individual builders for copying all the shared libraries and the program.
# That way all the copied files would be targets which would be erased by a
# scons clean, and they would be copied over if the system library source
# changed.  Oh well, this works for now.
# 

deploy_program_builder = Builder(action = deploy_program,
                                 emitter = deploy_program_emitter)


class DeployWarning(SCons.Warnings.Warning):
    pass


def generate(env):
    if 'DEPLOY_SHARED_LIBS' not in env:
        env['DEPLOY_SHARED_LIBS'] = []
    if 'DEPLOY_DIRECTORY' not in env:
        env['DEPLOY_DIRECTORY'] = "#deploy"
    env['BUILDERS']['DeployProgram'] = deploy_program_builder


def exists(env):
    return True

