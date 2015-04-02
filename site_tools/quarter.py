# -*- python -*-
import sys

def generate(env):
    env.Require('qt4')
    
    if sys.platform in ['linux', 'linux2']: 
        env.Append(CPPPATH=['/usr/local/include'])
        env.Append(LIBPATH=['/usr/local'])
        env.AppendUnique(LIBS=['Quarter', 'Coin'])
        

    if sys.platform == 'darwin':
        qtframes = ['QtGui', 'QtCore', 'QtOpenGL']
    
        env.AppendUnique(FRAMEWORKS=['Inventor', 'Quarter']+qtframes)
        
        if 'QT4DIR' in env:
            qtframeworkdir = env['QT4DIR']+'/Frameworks'
        else:
            qtframeworkdir = '/usr/local/Frameworks'
            
        env.AppendUnique(FRAMEWORKPATH=['/Library/Frameworks', qtframeworkdir])
        
        # Add paths directly to the qt headers, because the Quarter code include
        # statements don't specify the framework name.
        for f in qtframes:
            framepath = qtframeworkdir+'/'+f+'.framework/Headers'
            env.AppendUnique(CPPPATH=[framepath])
    
    if sys.platform == 'win32':
        env.AppendUnique(CXXFLAGS=["-DCOIN_NOT_DLL","-DQUARTER_NOT_DLL"])
        env.AppendUnique(LIBS=["Quarter", "Coin"])

def exists(env):
    return True

