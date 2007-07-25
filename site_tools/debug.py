
def generate(env):
    try:
        env.Debug(env)
    except:
        print "No debug tool found for this platform."
        pass

def exists(env):
    return True
