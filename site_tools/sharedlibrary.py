import os
import re
from SCons.Node.FS import Dir,File
from SCons.Script import Configure

def SharedLibrary3(env,target,sources,**kw):

    """ 
        For a reference on Linux conventions for shared library names see
        http://tldp.org/HOWTO/Program-Library-HOWTO/shared-libraries.html

        The usual convention is that the full library name is something like:
            libxxx.so.3.4
        The SONAME of the library is
            libxxx.so.3
        The basic library name, used when initially linking executables, is
            libxxx.so
        where 3 is the major number of the binary API and 4 is the minor number.

        Under linux, libxxx.so.3.4 is the actual library file, and libxxx.so.3
        and libxxx.so are symbolic links.

        The idea is that two libraries with the same name, same major
        number, but differing minor number implement the same binary API, and
        that a library with a new minor number could replace the old
        without breaking executable programs that depend on the library.

        From the man page of ld, discussing the -soname option:
        -soname=name
            When creating an ELF shared object, set the internal DT_SONAME field to
            the specified name.  When an executable is linked with a shared object
            which has a DT_SONAME field, then when the executable is run the dynamic
            linker will attempt to  load  the  shared object specified by the
            DT_SONAME field rather than the using the file name given to the linker.

        If the SONAME of a library contains just the major version number, and a
        a symbolic link exists with a name equal to the SONAME, pointing
        to the real library file, then a new library file could be installed
        with a different minor number, and the symbolic link updated to point
        to the new library, without re-linking executables.  This will only work
        if the binary APIs of libraries with the same major number are compatible.

        The SONAME of a library can be seen with
            objdump -p libxxx.so | grep SONAME

        ldd lists the SONAMEs of the libraries that a program was linked against.
        rpmbuild uses the same tools as ldd, and creates dependencies for
        executables based on the SONAMEs of the linked libraries.

        If the library has a SONAME, then the basic library name, libxxx.so,
        without major and minor numbers, is only used when linking executables
        with the -lxxx option.  That is why symbolic link .so's, without major
        and minor numbers, are sometimes found only in -devel RPMs.

        To create the above three libraries with this pseudo-builder, do:

            env['SHLIBMAJORVERSION'] = '3'
            env['SHLIBMINORVERSION'] = '4'
            libs = env.SharedLibrary3('xxx',objects)

        This builder will set the -soname in the real library file, and the other
        two will be symbolic links.

        To install the library and the symbolic links to a destination:

            env.SharedLibrary3Install('/opt/local/mystuff',libs)

        The libraries will be installed to subdirectory 'lib' or 'lib64' of
        /opt/local/mystuff, depending on whether the current environment
        builds 32 or 64 bit objects.

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

    try: 
        # convert dots to \. for regular expression
        shortsuffix = re.sub(r'\.',r'\\.',env['SHLIBSUFFIX'])

        fullsuffix = shortsuffix + re.sub(r'\.',r'\\.','.' + env['SHLIBMAJORVERSION'] + '.' + env['SHLIBMINORVERSION'])
    except KeyError:
        print "bug"
        throw

    target = env.Dir(target + '/' + env['LIBDIR'])

    nodes = []

    for src in source:
        # print "src.path=" + src.path
        full = re.search(fullsuffix + '$',str(src))
        if full != None and not os.path.islink(src.path):
            nodes.extend(env.Install(target,src))
        else:
            # from src.path get basic name of library: libxxx.so
            shortname = re.sub('(.+' + shortsuffix + ').*',r'\1',src.path)
            # print "shortname=" + shortname

            fullsrc = env.Dir('#').File(shortname + '.' + env['SHLIBMAJORVERSION'] + '.' + env['SHLIBMINORVERSION'])
            tgt = target.File(os.path.basename(src.path))
            env.Command(tgt,fullsrc,
                'cd $TARGET.dir; ln -sf $SOURCE.file $TARGET.file')
	    nodes.extend([tgt])

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
