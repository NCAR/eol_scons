import os

def generate(env):
    if os.path.exists("/etc/centos-release"):
        f = open("/etc/centos-release")
        line = f.readline()
        if " 7." in line:
            env.AppendUnique(CPPPATH=['/usr/include/jsoncpp'])

    env.Append(LIBS=['jsoncpp',])
        
def exists(env):
    return True

