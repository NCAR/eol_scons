import os
from symlink import MakeSymLink
from SCons.Node.FS import Dir,File
from SCons.Script import Configure,Builder,Action,Mkdir,Touch

def SharedLibrary3Emitter(target,source,env):
    """ 
        For a reference on Linux conventions for shared library names see
        http://tldp.org/HOWTO/Program-Library-HOWTO/shared-libraries.html

        The usual convention is that the full library name is something like:
            libxxx.so.X.Y
        Where X is the major version number of the binary API and Y is the minor version.

        The SONAME of the library is
            libxxx.so.X
        The basic library name, used when initially linking executables, is
            libxxx.so

        Under linux, libxxx.so.X.Y is typically the actual library file,
        and libxxx.so.X and libxxx.so are symbolic links.

        The idea is that two libraries with the same name, same major
        number, but differing minor number, implement the same binary API, and
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

        To create the above three libraries with this builder, do:

            env['SHLIBMAJORVERSION'] = '3'
            env['SHLIBMINORVERSION'] = '4'
            lib = env.SharedLibrary3('xxx',objects)

        This builder will set the -soname in the real library file, and the other
        two will be symbolic links.

        To install the library and the symbolic links to a destination:

            env.SharedLibrary3Install('/opt/mystuff',lib)

        If the environment token USE_ARCHLIBDIR is not defined, the
        libraries will be installed to /opt/mystuff/lib.  If USE_ARCHLIBDIR
        is defined, the libraries will be installed in /opt/mystuff/env['ARCHLIBDIR'].
        ARCHLIBDIR will have a value of "lib64" on linux 64 bit systems, otherwise
        "lib".

        As of this writing, this builder has only been tested on Linux.
        Support for other architectures needs to be added as necessary.
    """

    """
    In this emitter for SharedLibary3, target is the desired name of
    the library, like 'xxx'.
    source is the list of source or object files.

    Two construction variables must be defined for this builder:
    SHLIBMAJORVERSION and SHLIBMINORVERSION, which in the following
    examples are 'X' and 'Y'.
    
    This emitter registers a SharedLibrary builder for a target 'xxx' with
    the given source list of object and source files, link flags of
    '-Wl,-soname=libxxx.so.X' a and a shared library suffix of
    '.so.X.Y'. The SharedLibrary builder returns a target with the
    full name of 'libxxx.so.X.Y'

    This emitter then registers a symbolic link builder to link
    libxxx.so.X.Y to the soname libxxx.so.X.

    It then emits a target dependency of libxxx.so, and a source dependency
    of libxxx.so.X.Y. The target dependency is necesary if the user wants
    to do more with the library, such as install it with SharedLibrary3Install.
    
    The action of this builder then just has to complete the symbolic link
    from libxxx.so.X.Y to libxxx.so.

    If you try to register a symbolic link builder for libxxx.so in this
    emitter, you'll get a warning:
        Two different environments were specified for target libxxx.so,
        but they appear to have the same action:
    So we have to do the symbolic link in the action.
    """

    # libxxx.so
    # env['SHLIBPREFIX'] becomes $LIBPREFIX so use env.subst()
    libname = env.subst('$SHLIBPREFIX') + str(target[0]) + env['SHLIBSUFFIX']

    try:
        # libxxx.so.X
        soname = libname + '.' + env['SHLIBMAJORVERSION']
    except KeyError:
        print 'Cannot find SHLIBMAJORVERSION env variable'

    try:
        fulllib = env.SharedLibrary(str(target[0]),source,
            SHLINKFLAGS = env['SHLINKFLAGS'] + ['-Wl,-soname=' + soname],
            SHLIBSUFFIX = env['SHLIBSUFFIX'] +
                '.' + env['SHLIBMAJORVERSION'] +
                '.' + env['SHLIBMINORVERSION'])
    except KeyError:
        print 'Cannot find SHLIBMINORVERSION env variable'
        return None

    # For some reason we have to create the original target, otherwise:
    # scons: *** [x86] Implicit dependency `build_x86/util/nidas_util' not found,
    # needed by target `x86'.
    # 'util' is the directory containing the SConscript, whose variant_dir is
    # 'build_util'.
    # Creating an empty file named str(target[0]) on the variant_dir
    # satisfies scons.

    env.Command(target,source,
        [Mkdir('$TARGET.dir'),Touch('$TARGET')])

    # Register builder to create link to soname
    env.SymLink(soname,fulllib)

    # Don't register a builder here to create libname, like so:
    # env.SymLink(libname,fullname)
    # because you'll get a warning:
    # Two different environments were specified for target libxxx.so,
    #         but they appear to have the same action:

    return ([libname],[fulllib])

def SharedLibrary3Action(target,source,env):
    # This action just has to make the final symbolic link from
    # libxxx.so.X.Y to libxxx.so. Note it is done with an action,
    # not a builder, which would have created more dependencies.
    MakeSymLink(target,source,env)

    # If we ever want to completely replace the action of
    # SharedLibrary, here is its action, as found in
    # /usr/lib/scons/SCons/Defaults.py
    # ShLinkAction = SCons.Action.Action("$SHLINKCOM","$SHLINKCOMSTR")

    return 0

def SharedLibrary3Install(env,target,source,**kw):

    """
    Install source library to a library subdirectory of target.
    If env["USE_ARCHLIBDIR"] is defined, the source will be installed
    on target/$ARCHLIBDIR otherwise to target/lib.

    ARCHLIBDIR is defined as "lib64" on Linux 64 bit systems, otherwise "lib".

    See the discussion for SharedLibrary3 about how library versions 
    are handled.

    source should be a path like libxxx.so, which is what is returned
    as a target by the SharedLibrary3 builder.

    This installer will copy libxxx.so.$SHLIBMAJORVERSION.$SHLIBMINORVERSION
    to target/lib[64], and then create symbolic links on the target library directory:
        libxxx.so -> libxxx.so.$SHLIBMAJORVERSION.$SHLIBMINORVERSION
        libxxx.so.$SHLIBMAJORVERSION -> libxxx.so.$SHLIBMAJORVERSION.$SHLIBMINORVERSION
    """

    # add passed keywords to environment
    env = env.Clone(**kw)

    if env.has_key("USE_ARCHLIBDIR"):
        targetDir = env.Dir(target + '/' + env['ARCHLIBDIR'])
    else:
        targetDir = env.Dir(target + '/lib')

    # libname = source[0].path
    libname = str(source[0])
    try:
        soname = libname + '.' + env['SHLIBMAJORVERSION']
    except KeyError:
        print 'Cannot find SHLIBMAJORVERSION env variable'
        return None
    # print "SharedLibrary3Install, soname=" + soname

    try:
        fullname = soname + '.' + env['SHLIBMINORVERSION']
    except KeyError:
        print 'Cannot find SHLIBMINORVERSION env variable'
        return None
    # print "SharedLibrary3Install, fullname=" + fullname

    nodes = []
    tgt = env.Install(targetDir,fullname)
    nodes.extend(tgt)

    tgt = targetDir.File(os.path.basename(libname))
    nodes.extend(env.SymLink(tgt,fullname))

    tgt = targetDir.File(os.path.basename(soname))
    nodes.extend(env.SymLink(tgt,fullname))
    
    # return list of targets which can then be used in an Alias
    return nodes

def generate(env):

    # Add builder and installer for shared libraries
    builder = Builder(action=SharedLibrary3Action,emitter=SharedLibrary3Emitter)
    env.Append(BUILDERS = {"SharedLibrary3": builder})

    env.AddMethod(SharedLibrary3Install)

    # ARCHLIBDIR can be used if the user wants to install libraries
    # to a special directory for the architecture, like lib64
    sconf = Configure(env)
    libdir = 'lib'
    if sconf.CheckTypeSize('void *',expect=8,language='C'):
        libdir = 'lib64'
    sconf.env.Append( ARCHLIBDIR = libdir)
    env = sconf.Finish()

def exists(env):
    return 1
