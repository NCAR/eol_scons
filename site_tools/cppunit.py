
def generate(env):
    # Don't try here to make things unique in LIBS and CFLAGS; just do a 
    # simple append
    env.ParseConfig('cppunit-config --cflags --libs', unique = False)
    # needed for FC2
    env.AppendLibrary("dl")



def exists(env):
    return True

