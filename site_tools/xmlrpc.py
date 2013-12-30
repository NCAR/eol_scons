import os

def generate(env):

    # If xmlrpcpp pkg-config file exists, which is installed by the
    # xmlrpc++ RPM, this should be all that's necessary
    if (os.system('pkg-config --exists xmlrpcpp') == 0):
        env.ParseConfig('pkg-config --cflags --libs xmlrpcpp')
        return

    # There are some older packages with the newer library file name
    # but without the pkg-config files, so those must be found by
    # explicitly searching for them under /usr.

    # grope around for the XMLRPC C++ libraries.
    # In xmlrpc++ RPMs up to 0.7-3:
    #    o headers are under /usr/include/xmlrpc++
    #    o library is /usr/lib{,64}/libxmlrpc++.so
    # For 0.7-4 and later:
    #    o headers are under /usr/include/xmlrpcpp
    #    o library is /usr/lib{,64}/libxmlrpcpp.so
    # The change was necessary because the new (and common)
    # xmlrpc-c-c++ package contains a /usr/lib/libxmlrpc++.so that
    # supports a different API than the xmlrpc++ package.

    # All systems should be updated to at least 0.7-4 by now,
    # so don't check for /usr/lib{,64}/libxmlrpc++.so, even when
    # the xmlrpc++ RPM is installed.

    # Removed exec of rpm -q to check for the package, to be compatible
    # with debian systems.

    # if pkg-config file doesn't exist, look in the usual places
    paths = [ '/usr/lib64', '/usr/lib' ]
    prefix = env.get('OPT_PREFIX')
    found = False
    if prefix:
        paths[:0] = [ prefix + '/lib64', prefix + '/lib' ]
    for libpath in paths:
        prefix = os.path.dirname(libpath)
        if (os.path.exists(os.path.join(libpath,'libxmlrpcpp.so'))):
            env.AppendUnique(CPPPATH = [os.path.join(prefix,'include','xmlrpcpp')])
            if prefix != '/usr':
                env.AppendUnique(LIBPATH=[libpath])
            env.Append(LIBS=['xmlrpcpp'])
            found = True
            break

    if not found:
        # if built and installed from the original source, the library
        # is called libXmlRpc.a
        env.AppendUnique(CPPPATH=[os.path.join(prefix, 'include','XmlRpc')])
        env.AppendUnique(LIBPATH=[os.path.join(prefix, 'lib')])
        env.Append(LIBS=['XmlRpc'])

def exists(env):
    return True

