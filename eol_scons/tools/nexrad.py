# -*- python -*-
import os,os.path

NEXRAD_DIR='/opt/nexrad'


def Install_Nexrad_Scripts(self):
    from glob import glob1
    tmp = glob1('scripts','*')
#    print 'tmp = ', tmp
    flist = []
    for t in tmp:
        if not t == 'CVS':
            flist.append(os.path.join('scripts', t))
#    print 'flist = ', flist
            
    self.Install(os.path.join(NEXRAD_DIR, 'bin'), flist)

def generate(env):
    env.AddMethod(Install_Nexrad_Scripts)


# Export("NEXRAD_DIR")

def exists(env):
    return True

