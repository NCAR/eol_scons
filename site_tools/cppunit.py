
def generate(env):
    env.ParseConfig('cppunit-config --cflags --libs')
    # needed for FC2
    env.AppendLibrary("dl")



def exists(env):
    return True

