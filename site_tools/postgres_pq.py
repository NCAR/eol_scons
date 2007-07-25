

def generate(env):
    env.Append(DEPLOY_SHARED_LIBS='pq')
    env.Append(LIBS=['pq',])

def exists(env):
    return True

