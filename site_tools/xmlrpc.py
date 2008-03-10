import os

def generate(env):
    # If the EOL xmlrpc++ RPM is installed, then headers are under 
    # /usr/include/xmlrpc++, and we assume they are included explicitly
    # with the xmlrpc++ directory: "#include <xmlrpc++/XmlRpc.h>".  
    # Hence, no -I is needed in CFLAGS.  The library is in 
    # /usr/lib/libxmlrpc++.a (or .so).
    if (os.system('rpm -V --quiet xmlrpc++') == 0):
        env.Append(LIBS=['xmlrpc++'])
                         
    # If no RPM, then assume headers are under OPT_PREFIX/include, and
    # the library is in OPT_PREFIX/lib/libXmlRpc.a.
    else:
        env.AppendUnique(CPPPATH=[os.path.join(env['OPT_PREFIX'],'include')])
        env.AppendUnique(LIBPATH=[os.path.join(env['OPT_PREFIX'],'lib')])
        env.Append(LIBS=['XmlRpc',])



def exists(env):
    return True

