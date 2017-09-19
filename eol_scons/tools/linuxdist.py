from __future__ import print_function

import sys
import re
import os

def GetRhDistribution():

    distmap = {
        'Taroon':'ws3',
        'Nahant':'el4',
        'Shrike':'rh9',
        'Tettnang':'fc2',
        'Heidelberg':'fc3',
        'Stentz':'fc4',
        'Pre-FC4':'fc3',
        'Bordeaux':'fc5',
        'Zod':'fc6'
        }

    dist = sys.platform
    try:
        fd = open("/etc/redhat-release",'r')
        distribution = fd.read()
        fd.close()
        for k in distmap.keys():
            if re.search(k, distribution):
                dist = distmap[k]
                break
        if not dist:
            print("Red Hat distribution is unknown.")
    except IOError:
        pass
    return dist

linuxdist = GetRhDistribution()

def SetRhDistribution(env):

    dist = GetRhDistribution()
    env['DISTRIBUTION'] = dist

def generate(env):
    SetRhDistribution(env)

def exists(env):
    return os.path.exists("/etc/redhat-release")

