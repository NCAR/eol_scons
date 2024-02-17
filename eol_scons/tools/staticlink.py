"""
Specify static linking for specific libraries.

Applying this tool inserts another wrapper function around the _LIBFLAGS
construction variable.  Normally that variable expands to the list of
library link options, with the usual option prefixes like -l.  The wrapper
then replaces link options for the static libraries with options to force
static linking.  The static libraries can be specified with the
StaticLink() method of the environment, or appended to the
STATIC_LIBRARY_NAMES variable.  Any LIBFLAGS option in which that library
name appears will be converted to static linking options.

The original idea was to insert static link options around the library link
option, like -Wl,-Bstatic and -Wl,-Bdynamic.  However, the OSX clang linker
does not provide equivalent options, and it always prefers dynamic over
static, so that approach does not work.  We're stuck with explicitly
providing the static library filename in the link command, which seems to
be the only portable approach.

There are suggestions on the web like putting links to static libraries in
a special directory, and then specifying that library first in the library
paths.  However, that sounds like a rather more complicated kludge than
just looking for the static library file and adding it explicitly.  We know
that putting a library static archive on the command-line works on both OSX
and Linux.

...and I suppose it's more likely to work on Windows also, if that turns
out to be necessary also.
"""

import SCons

_syspaths = ['/usr/lib64', '/usr/lib']


def _insert_static_flags(env):
    """
    Grab the LIBFLAGS list and insert static flags around the specified
    libraries.
    """
    libs = env.subst("$save_for_static_LIBFLAGS").split()
    modlibs = []
    for libopt in libs:
        found = [libname for libname in env.get('STATIC_LIBRARY_NAMES', [])
                 if libname in libopt]
        if found:
            modlibs.extend(['-Wl,-Bstatic', libopt, '-Wl,-Bdynamic'])
        else:
            modlibs.append(libopt)
    return modlibs


# One potential advantage of this approach is that we know here if a static
# library is not available and can give a more useful explanation, rather
# than just getting an error message from the compiler that a library could
# not be found.

def _replace_static_libraries(env):
    """
    Replace the library link options for static libraries with the actual
    path to the static archive library.
    """
    libs = env.subst("$save_for_static_LIBFLAGS").split()
    modlibs = []
    libprefix = env.get("LIBPREFIX")  # eg 'lib'
    libsuffix = env.get("LIBSUFFIX")  # eg '.a'
    liblinkprefix = env.get("LIBLINKPREFIX")  # eg '-l'
    liblinksuffix = env.get("LIBLINKSUFFIX")  # eg ''

    libpath = env.get('LIBPATH', [])
    searchpaths = libpath[:]
    # This is a kludge but a sort of failsafe, since the primary motivation
    # for this tool is to get static linking of boost_serialization, and so
    # on OSX this is equivalent to the original working fix of hardcoding
    # the boost path according to where brew puts it.  This is not
    # necesssary if LIBPATH already contains it, but I don't want to risk
    # breaking on OSX yet again.
    if env['PLATFORM'] == 'darwin':
        searchpaths.append('/usr/local/opt/boost/lib')
    searchpaths.extend(_syspaths)

    staticlibnames = env.get('STATIC_LIBRARY_NAMES', [])
    for libopt in libs:
        found = [libname for libname in staticlibnames if libname in libopt]

        # It's possible this is already a file path and not a link option.
        if not found or not libopt.startswith(liblinkprefix):
            modlibs.append(libopt)
            continue

        # So we have a library option that matches, build up the static
        # library name and look for it in the paths.
        libname = libopt.lstrip(liblinkprefix)
        libname = libname.rstrip(liblinksuffix)
        libfile = libprefix + libname + libsuffix

        libnode = env.FindFile(libfile, searchpaths)
        if not libnode:
            msg = str("Static library archive %s could "
                      "not be found." % (libfile))
            if "boost" in found[0]:
                msg += "  Install boost-static?"
            raise SCons.Errors.StopError(msg)
        modlibs.append(libnode.get_abspath())

    return modlibs


def _append_library(env, libname):
    env.PrintProgress("Requiring static linking for %s." % (libname))
    env.AppendUnique(STATIC_LIBRARY_NAMES=[libname])


def generate(env):
    if 'save_for_static_LIBFLAGS' in env:
        return
    env['save_for_static_LIBFLAGS'] = env['_LIBFLAGS']
    env['_LIBFLAGS'] = "${_replace_static_libraries(__env__)}"
    env['_insert_static_flags'] = _insert_static_flags
    env['_replace_static_libraries'] = _replace_static_libraries
    env.AddMethod(_append_library, "StaticLink")


def exists(env):
    return True
