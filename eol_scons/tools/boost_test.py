
import os

# boost::test as of 1.34 changes the interface for supplying the main()
# function to test programs when the test library is dynamically linked,
# and that doesn't work with our existing usage.  One fix is to link with
# the static library, which does supply the main() function.  A code
# solution which is portable between pre and post 1.34 has not been worked
# out yet, so this looks like the easiest workaround for now.  It allows
# pre 1.34 installs to work as before, while 1.34 and after need to install
# the boost-devel-static package.

def generate(env):
    slib='/usr/lib/libboost_unit_test_framework.a'
    env.Require('boost')
    if False and os.path.exists(slib):
        env.Append (LIBS = [env.File(slib)])
    else:
        env.Append (LIBS = ['boost_unit_test_framework'])

def exists(env):
    return True



