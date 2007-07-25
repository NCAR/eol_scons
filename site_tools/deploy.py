import os
import re
import SCons
from SCons.Builder import Builder
from SCons.Action import Action
import shutil

def makedirs(dir):
    try:
        print "mkdir ", dir
        os.makedirs(dir)
    except:
        if not os.access(dir, os.W_OK): raise


def ldd(program_node, env):
    "Return a map with each dependent library name and its location."
    libraries = {}
    # Run ldd on the program
    lddout = os.popen("ldd %s" % (program_node.get_abspath())).read()
    # Get the list of library keys to include
    libkeys = env['DEPLOY_SHARED_LIBS']
    libdir = os.path.join(env['DEPLOY_DIRECTORY'],"lib")
    for k in libkeys:
        # If the library is in the dependencies, then the file will
        # be copied into the deploy lib directory
        match = re.search(r"lib%s\..*=> (.+) \(" % env.subst(k),
                          lddout, re.MULTILINE)
        if match:
            lib = env.File(match.group(1))
            if not libraries.has_key(lib.name):
                print "Found", lib
                libraries[lib.name] = lib
                libraries.update (ldd(lib, env))
    return libraries


def deploy_program_emitter(target, source, env):
    "Given a source program, calculate the targets."
    # We don't know the dependencies until the program has been linked,
    # thus we can't use an emitter to calculate the targets that will
    # be copied into the deploy directory.  So the only target we can
    # generate now is the copy of the program itself.
    bindir = os.path.join(env['DEPLOY_DIRECTORY'],"bin")
    dest = os.path.join(bindir,source[0].name)
    return dest, source


def deploy_program(target, source, env):

    """Copy a program target into a deploy tree along with all of its
    dynamic dependencies."""
    bindir = os.path.join(env['DEPLOY_DIRECTORY'],"bin")
    libdir = os.path.join(env['DEPLOY_DIRECTORY'],"lib")
    makedirs(bindir)
    makedirs(libdir)
    progdest = os.path.join(bindir,source[0].name)
    libraries = ldd(source[0], env)
    shutil.copy(str(source[0]), progdest)
    for k in libraries:
        file = libraries[k]
        libdest = os.path.join(libdir, file.name)
        print "copy (%s,%s)" % (str(file), libdest)
        shutil.copy(str(file), libdest)


def deploy_program_message(target, source, env):
    return "Deploying %s into %s." % (source[0], env['DEPLOY_DIRECTORY'])


variables = ['DEPLOY_DIRECTORY', 'DEPLOY_SHARED_LIBS']

deploy_program_builder = Builder(action = Action(deploy_program,
                                                 deploy_program_message,
                                                 variables),
                                 emitter = deploy_program_emitter)


class DeployWarning(SCons.Warnings.Warning):
    pass


def generate(env):
    if not env.has_key('DEPLOY_SHARED_LIBS'):
        env['DEPLOY_SHARED_LIBS'] = []
    if not env.has_key('DEPLOY_DIRECTORY'):
        env['DEPLOY_DIRECTORY'] = str(env.Dir("#deploy"))
    env['BUILDERS']['DeployProgram'] = deploy_program_builder


def exists(env):
    return True

