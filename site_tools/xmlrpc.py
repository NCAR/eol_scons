import os

def generate(env):
    # See if the EOL xmlrpc++ RPM is installed.  If so, then up to 0.7-3:
    #    o headers are under /usr/include/xmlrpc++
    #    o library is /usr/lib/libxmlrpc++.so
    # For 0.7-4 and later:
    #    o headers are under /usr/include/xmlrpcpp
    #    o library is /usr/lib/libxmlrpcpp.so
    # The change was necessary because the new (and common) xmlrpc-c package
    # contains a /usr/lib/libxmlrpc++.so that supports a different API than
    # the xmlrpc++ package.
    if (os.system('rpm -V --quiet xmlrpc++') == 0):
        # Check for libxmlrpcpp.so in both /usr/lib and /usr/lib64, so
        # we're covered for both 32-bit and 64-bit installations.
        if (os.path.exists("/usr/lib/libxmlrpcpp.so") or 
            os.path.exists("/usr/lib64/libxmlrpcpp.so")):
            env.Append(LIBS=['xmlrpcpp'])
#            env.AppendUnique(DEPLOY_SHARED_LIBS=['xmlrpcpp'])
            env.AppendUnique(CPPPATH = ['/usr/include/xmlrpcpp'])
        else:
            env.Append(LIBS=['xmlrpc++'])
            env.AppendUnique(CPPPATH = ['/usr/include/xmlrpc++'])
                         
    # If no RPM, then assume headers are under OPT_PREFIX/include, and
    # the library is in OPT_PREFIX/lib/libXmlRpc.a.
    else:
        env.AppendUnique(CPPPATH=[os.path.join(env['OPT_PREFIX'],'include')])
        env.AppendUnique(LIBPATH=[os.path.join(env['OPT_PREFIX'],'lib')])
        env.Append(LIBS=['XmlRpc',])



def exists(env):
    return True

