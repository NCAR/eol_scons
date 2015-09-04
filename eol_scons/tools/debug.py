
def generate(env):
    try:
        env.Debug()
    except:
        print "No debug tool found for this platform."
        pass

def exists(env):
    return True
