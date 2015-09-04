
def generate(env):
    try:
        env.Warnings()
    except:
        print "No Warnings tool found for this platform."
        pass

def exists(env):
    return True
