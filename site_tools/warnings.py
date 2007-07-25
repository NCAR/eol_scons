
def generate(env):
    try:
        env.Warnings(env)
    except:
        print "No Warnings tool found for this platform."
        pass

def exists(env):
    return True
