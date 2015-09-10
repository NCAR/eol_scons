# link in Electric Fence library to debug memory problems

def generate(env):
        env.Append(LIBS=['efence',])
        
        

def exists(env):
    return True

