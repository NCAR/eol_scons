
def generate(env):
    try:
        env.Profile(env)
    except:
        print "No profile tool found for this platform."
        pass

def exists(env):
    return True
