# -*- python -*-
import sys

def generate(env):
    env.Require('coin')
    env.Require(['qtgui', 'qtcore', 'qtwidgets', 'qtopengl', 'qwt'])
    env.AppendUnique(LIBS=['Quarter'])

    if sys.platform in ['linux', 'linux2']: 
        pass

    if sys.platform == 'darwin':
        qtframes = ['QtGui', 'QtCore', 'QtWidget', 'QtOpenGL']
        if 'QT4DIR' in env:
            qtframeworkdir = env['QT4DIR']+'/Frameworks'
        else:
            qtframeworkdir = '/usr/local/opt/qt5/Frameworks'
            
        env.AppendUnique(FRAMEWORKPATH=['/Library/Frameworks', qtframeworkdir])
        
        # Add paths directly to the qt headers, because the Quarter code include
        # statements don't specify the framework name.
        for f in qtframes:
            framepath = qtframeworkdir+'/'+f+'.framework/Headers'
            env.AppendUnique(CPPPATH=[framepath])

        env.AppendUnique(LIBS=["Quarter"])
    
    if sys.platform == 'msys':
        env.AppendUnique(CXXFLAGS=["-DQUARTER_NOT_DLL"])
        env.Append(LIBS=["Quarter"])
        env.Append(LIBS=["Qt5Widgets"])
        env.Append(LIBS=["Qt5Gui"])
        env.Append(LIBS=["Qt5OpenGL"])

def exists(env):
    return True

