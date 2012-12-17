import os

def generate(env):

    # If xmlrpcpp pkg-config file exists, which is installed by the
    # xmlrpc++ RPM, this should be all that's necessary
    if (os.system('pkg-config --exists xmlrpcpp') == 0):
        env.ParseConfig('pkg-config --cflags --libs xmlrpcpp')
        return

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
    prefix = env.get('OPT_PREFIX')
    if not prefix:
        prefix = '/usr'

    libpath = os.path.join(prefix, 'lib')
    libpath64 = os.path.join(prefix, 'lib64')
    if (os.path.exists(os.path.join(libpath,'libxmlrpcpp.so'))):
        env.AppendUnique(CPPPATH = [os.path.join(prefix,'include','xmlrpcpp')])
        if prefix != '/usr':
            env.AppendUnique(LIBPATH=[libpath])
        env.Append(LIBS=['xmlrpcpp'])

    elif (os.path.exists(os.path.join(libpath64,'libxmlrpcpp.so'))):

        env.AppendUnique(CPPPATH = [os.path.join(prefix,'include','xmlrpcpp')])
        if prefix != '/usr':
            env.AppendUnique(LIBPATH=[libpath64])
        env.Append(LIBS=['xmlrpcpp'])

    else:
        # if built and installed from the original source, the library
        # is called libXmlRpc.a
        env.AppendUnique(CPPPATH=[os.path.join(prefix, 'include','XmlRpc')])
        env.AppendUnique(LIBPATH=[os.path.join(prefix, 'lib')])
        env.Append(LIBS=['XmlRpc'])

def exists(env):
    return True

