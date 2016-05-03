import os

def generate(env):

    # For cases where we want to override the system installation with a
    # local build for debugging, the source directory can be specified with
    # the XMLRPCPP_SOURCE_PATH environment variable.
    debugpath = env.get('XMLRPCPP_SOURCE_PATH')
    if debugpath:
        # Include headers directly from the src directory and link to the
        # static library with debug symbols.
        env.AppendUnique(CPPPATH = os.path.join(debugpath, 'src'))
        env.Append(LIBS = env.File(os.path.join(debugpath, 'libXmlRpcpp.a')))
        return

    # If xmlrpcpp pkg-config file exists, which is installed by the
    # xmlrpc++ RPM, this should be all that's necessary

    # In order to test for a pkg-config file, you can't just do
    #   os.system('pkg-config --exists xmlrpcpp')
    # since that won't get PKG_CONFIG_PATH from env['ENV'].
    # Instead:
    #   subprocess.Popen(['pkg-config','xmlrpcpp'],env=env['ENV']).wait()
    # or
    #   env.Execute('pkg-config xmlrpcpp')
    # but I don't know how to suppress the "scons: "*** Error" message
    # from the latter.
    #
    # Likewise you can catch the OSError exception from ParseConfig,
    # but there doesn't seem to be a way to suppress the error message,
    # which looks like:
    #   Package xmlrpcpp was not found in the pkg-config search path.
    #   Perhaps you should add the directory containing `xmlrpcpp.pc'
    #   to the PKG_CONFIG_PATH environment variable
    #   No package 'xmlrpcpp' found

    # For speed, and since that error message may lead folks to make
    # more use of pkg-config :-), we're not doing the double check here.

    try:
        env.ParseConfig('pkg-config --cflags --libs xmlrpcpp')
        return
    except OSError:
        pass

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

