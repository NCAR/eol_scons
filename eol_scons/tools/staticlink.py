"""
Specify static linking for specific libraries.

Applying this tool inserts another wrapper function around the _LIBFLAGS
construction variable.  Normally that variable expands to the list of
library link options, with the usual option prefixes like -l.  The wrapper
then inserts static link options around the static libraries.  The static
libraries can be specified with the StaticLink() method of the environment,
or appended to the STATIC_LIBRARY_NAMES variable.  Any LIBFLAGS option in
which that library name appears will be surrounded with static link
options.

Currently this only inserts the GNU toolchain options for static linking.
"""

def _insert_static_flags(env):
    """
    Grab the LIBFLAGS list and insert static flags around the specified
    libraries.
    """
    libs = env.subst("$save_for_static_LIBFLAGS").split()
    # print("LIBFLAGS before insertion: %s" % (" ".join(libs)))
    modlibs = []
    for libopt in libs:
        found = [libname for libname in env.get('STATIC_LIBRARY_NAMES', [])
                 if libname in libopt]
        if found:
            modlibs.extend(['-Wl,-Bstatic', libopt, '-Wl,-Bdynamic'])
        else:
            modlibs.append(libopt)
    # print("LIBFLAGS after insertion: %s" % (" ".join(modlibs)))
    return modlibs


def _append_library(env, libname):
    print("Requiring static linking for %s." % (libname))
    env.AppendUnique(STATIC_LIBRARY_NAMES=[libname])


def generate(env):
    if env.has_key('save_for_static_LIBFLAGS'):
        return
    # print("Adding StaticLink to this environment.")
    env['save_for_static_LIBFLAGS'] = env['_LIBFLAGS']
    env['_LIBFLAGS'] = "${_insert_static_flags(__env__)}"
    env['_insert_static_flags'] = _insert_static_flags
    env.AddMethod(_append_library, "StaticLink")


def exists(env):
    return True
