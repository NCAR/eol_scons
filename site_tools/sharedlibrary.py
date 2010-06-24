import os
import re
import tempfile
import subprocess
from SCons.Node.FS import Dir,File
from SCons.Script import Configure

def SharedLibrary3(env,target,sources,**kw):

    """ 
        This SCons pseudo builder will build a shared library with name

        env["SHLIBPREFIX"] + target + env["SHLIBSUFFIX"] + '.' +
            env["SHLIBMAJORVERSION"] + '.' env["SHLIBMINORVERSION"] + '.'

        The library will be built with a soname linker option:
        -soname env["SHLIBPREFIX"] + target + env["SHLIBSUFFIX"] + '.' + env["SHLIBMAJORVERSION"]

        The SCons environment variables SHLIBPREFIX, SHLIBSUFFIX are pre-defined for you.
        On linux SHLIBPREFIX='lib' and SHLIBSUFFIX='.so'.

        Then create 2 symbolic links to that library.

        For a reference on Linux conventions for shared library names see
        http://tldp.org/HOWTO/Program-Library-HOWTO/shared-libraries.html

        The typical convention is that the full library name is something like:
            libxxx.so.3.4
        The SONAME is
            libxxx.so.3
        And the basic library name is
            libxxx.so
        where 3 is the major number of the binary API and 4 is the minor number.

        Under linux, libxxx.so.3.4 is the actual library file, and libxxx.so.3
        and libxxx.so are symbolic links.

        To create the above three libraries, do:

            env['SHLIBMAJORVERSION'] = '3'
            env['SHLIBMINORVERSION'] = '4'
            libs = env.SharedLibrary3('xxx',objects)

        To install the library and the symbolic links to a destination:

            env.SharedLibrary3Install('/opt/local/mystuff',libs)

        The libraries will be installed to subdirectory 'lib' or 'lib64' of
            /opt/local/mystuff, depending on whether the current environment
            builds 64 or 32 bit objects.

        Note that the initial version of this tool is directed at Linux.
        Support for other architectures needs to be added as necessary.
    """

    # add passed keywords to environment
    env = env.Clone(**kw)

    # target argument here is a simple string
    libname = env.subst('${SHLIBPREFIX}' + target + '$SHLIBSUFFIX')
    try:
        soname = libname + '.' + env['SHLIBMAJORVERSION']
    except KeyError:
        print 'Cannot find SHLIBMAJORVERSION env variable'
        return None

    try:
        fullname = soname + '.' + env['SHLIBMINORVERSION']
    except KeyError:
        print 'Cannot find SHLIBMINORVERSION env variable'
        return None

    nodes = []
    # build the shared library with full .so.MAJOR.MINOR suffix
    # and a -soname linker option pointing to .so.MAJOR
    # kw['SHLINKFLAGS'] = env['SHLINKFLAGS'] + ['-Wl,-soname=' + soname]
    # kw['SHLIBSUFFIX'] = env['SHLIBSUFFIX'] + '.' + env['SHLIBMAJORVERSION'] + '.' + env['SHLIBMINORVERSION']
    # nodes.extend(env.SharedLibrary(target,sources,**kw))
    nodes.extend(env.SharedLibrary(target,sources,
        SHLINKFLAGS = env['SHLINKFLAGS'] + ['-Wl,-soname=' + soname],
        SHLIBSUFFIX = env['SHLIBSUFFIX'] + '.' + env['SHLIBMAJORVERSION'] + '.' + env['SHLIBMINORVERSION']))
    # print 'nodes[0]=' + str(nodes[0])

    # symbolic links
    nodes.extend(env.Command(libname,fullname,'cd $TARGET.dir; ln -sf $SOURCE.file $TARGET.file'))
    nodes.extend(env.Command(soname,fullname,'cd $TARGET.dir; ln -sf $SOURCE.file $TARGET.file'))

    return nodes

def SharedLibrary3Install(env,target,source,**kw):

    # SharedLibraries returns the library targets in this order:
    #   1. libname: SHLIBPREFIX + name + SHLIBSUFFIX: libxxx.so
    #   2. soname: libname + '.' + SHLIBMAJORVERSION: libxxx.so.3
    #   3. fullname: libname + '.' + SHLIBMINORVERSION: libxxx.so.3.2
    # Fullname should be the actual library, the others are symbolic links to fullname.
    # We'll use regular expressions and os.path.islink() to determine which is which.

    # add passed keywords to environment
    env = env.Clone(**kw)

    fullsrc = None

    try: 
        libsuffix = env['SHLIBSUFFIX'] + '.' + env['SHLIBMAJORVERSION'] + '.' + env['SHLIBMINORVERSION']
    except KeyError:
        print "bug"
        throw

    # look for a source ending in .so.MAJOR.MINOR
    for src in source:
        # print "src=" + str(src)
        full = re.search(libsuffix + '$',str(src))
        if full != None and not os.path.islink(src.path):
            fullsrc = src
            break

    # Can't find a library with the right suffix, that isn't a symbolic link.
    if fullsrc == None:
        print 'Cannot find shared library with suffix ' + libsuffix + ' to install'
        throw

    target = env.Dir(target + '/' + env['LIBDIR'])

    nodes = []
    nodes.extend(env.Install(target,fullsrc))

    for src in source:
        # print "src=" + str(src)
        if os.path.islink(src.path):
            nodes.extend(env.Command(target.File(src.path),fullsrc,
                'cd $TARGET.dir; ln -sf $SOURCE.file $TARGET.file'))

    return nodes


def generate(env):

    # Add pseudo builders for shared libraries
    env.AddMethod(SharedLibrary3)
    env.AddMethod(SharedLibrary3Install)

    sconf = Configure(env)
    libdir = 'lib'
    if sconf.CheckTypeSize('void *',expect=8,language='C'):
        libdir = 'lib64'
    sconf.env.Append( LIBDIR = libdir)
    env = sconf.Finish()
    return libdir

def exists(env):
    return 1
