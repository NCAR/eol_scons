# -*- python -*-
import sys

def generate(env):
    env.Require('qt5')
    env.Require('coin')
    
    if sys.platform in ['linux', 'linux2']: 
        # There is no need to set specific include or library paths here.
        # It is enough to require the coin tool above, since Quarter
        # installs into the same location.  When built from source, both
        # install into the default configure prefix of /usr/local/.  When
        # installed as an RPM, Quarter headers are in /usr/include/Coin2
        # and the Quarter library is in the same place as the Coin library.
        env.AppendUnique(LIBS=['Quarter'])

    if sys.platform == 'darwin':
        env.AppendUnique(LIBS=['Quarter'])
        qtframes = ['QtGui', 'QtCore', 'QtWidget', 'QtOpenGL']
#    
#        env.AppendUnique(FRAMEWORKS=['Inventor', 'Quarter']+qtframes)
#        
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
        env.AppendUnique(CPPPATH=["/mingw64/include/qwt"])
        env.Append(LIBS=["Quarter"])
        env.Append(LIBS=["Qt5Widgets"])
        env.Append(LIBS=["Qt5Gui"])
        env.Append(LIBS=["Qt5OpenGL"])
        env.Append(LIBPATH=["/usr/local/bin"])


def exists(env):
    return True

