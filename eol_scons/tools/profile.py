from __future__ import print_function

def generate(env):
    try:
        env.Profile()
    except:
        print("No profile tool found for this platform.")
        pass

def exists(env):
    return True
