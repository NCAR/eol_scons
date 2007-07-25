
def generate(env):
    try:
        env.Optimize(env)
    except:
        print "No optimize tool found for this platform."
        pass

def exists(env):
    return True
