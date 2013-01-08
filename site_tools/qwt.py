
import os
import SCons
from SCons.Variables import PathVariable
from SCons.Script import Configure
import eol_scons.chdir
from eol_scons.package import Package
import string
import platform


_options = None
myKey = 'HAS_PACKAGE_QWT'
USE_PKG_CONFIG = 'Using pkg-config'

# The header files are unpacked directly into the QWTDIR/include
# directory, and thus are listed as targets of the Unpack builder.
# Otherwise, if they are emitted as targets of the qwt_builder, scons will
# remove the headers before attempting to build them.  We could try to use
# Precious() on them, but this is more accurate anyway.

qwt_headers = string.split("""
qwt.h		  qwt_double_rect.h	 qwt_picker.h		 qwt_scale.h
qwt_analog_clock.h qwt_drange.h	 qwt_picker_machine.h	 qwt_scldiv.h
qwt_array.h	  qwt_dyngrid_layout.h qwt_plot.h		 qwt_scldraw.h
qwt_arrbtn.h	  qwt_event_pattern.h  qwt_plot_canvas.h	 qwt_sclif.h
qwt_autoscl.h	  qwt_global.h	 qwt_plot_classes.h	 qwt_sldbase.h
qwt_compass.h	  qwt_grid.h		 qwt_plot_dict.h	 qwt_slider.h
qwt_compass_rose.h qwt_knob.h		 qwt_plot_item.h	 qwt_spline.h
qwt_counter.h	  qwt_layout_metrics.h qwt_plot_layout.h	 qwt_symbol.h
qwt_curve.h	  qwt_legend.h	 qwt_plot_picker.h	 qwt_text.h
qwt_data.h	  qwt_marker.h	 qwt_plot_printfilter.h qwt_thermo.h
qwt_dial.h	  qwt_math.h		 qwt_plot_zoomer.h	 qwt_wheel.h
qwt_dial_needle.h  qwt_paint_buffer.h	 qwt_push_button.h
qwt_dimap.h	  qwt_painter.h	 qwt_rect.h
""")

qwt_actions = [
    "QTDIR=$QTDIR $QTDIR/bin/qmake qwt.pro",
    "QTDIR=$QTDIR make"
    ]

def is_64bit():
  """ is this a 64-bit system? """
  return platform.machine()[-2:] == '64'

if is_64bit():
    lib_= 'lib64'
else:
    lib_= 'lib'

class QwtPackage(Package):

    def __init__(self):
        headers = [os.path.join("include",f) for f in qwt_headers]
        libs = ["$QWTDIR/"+lib_+"/libqwt.so"]
        Package.__init__(self, "QWT", ["qwt.pro"]+headers,
                         qwt_actions, libs,
                         default_package_file = "qwt-4.2.0.zip")
        self.settings = {}

    def checkBuild(self, env):
        if env['PLATFORM'] == 'win32':
            return
        qwt_dir = env['QWTDIR']
        libqwt = os.path.join(qwt_dir, lib_, 'libqwt.so')
        if not os.access(libqwt, os.R_OK):
            # Not installed in the given QWTDIR, so try internal path
            qwt_dir = self.getPackagePath(env)
            env['QWTDIR'] = qwt_dir
        Package.checkBuild(self, env)


    def require(self, env):
        env.Tool('download')
        env.Tool('unpack')
        if not self.settings:
            import new
            env.EnableQwt = new.instancemethod(enable_qwt, env, type(env))
            self.calculate_settings(env)
        self.apply_settings(env)

    def calculate_settings(self, env):

        qwt_dir = find_qwtdir(env)
        if not qwt_dir:
            return

        # The actual QWTDIR value to use depends upon whether qwt is being
        # built internally or not.  Check here to see if the QWTDIR option
        # points to an existing library, and if not then resort to the
        # package build location.

        Package.checkBuild(self, env)
        self.settings['QWTDIR'] = qwt_dir
        qwt_libdir = os.path.join(qwt_dir, lib_)
        libqwt = os.path.join(qwt_libdir, 'libqwt.so')

        # These settings apply whether building, locating manually, or
        # locating with pkg-config
        qwt_docdir = os.path.join(qwt_dir, 'doc', 'html')
        self.settings['QWT_DOXREF'] = 'qwt:' + qwt_docdir

        if (qwt_dir == USE_PKG_CONFIG):
            return
            
        if env['PLATFORM'] != 'darwin':
        	if self.building:
        		self.settings['LIBS'] = [env.File(libqwt)]
        	else:
        		self.settings['LIBS'] = ['qwt']
        		self.settings['LIBPATH'] = [qwt_libdir]
        else:
          if env['PLATFORM'] == 'darwin':
        	env.Require('qt4')
        	env.AppendUnique(FRAMEWORKPATH=['/usr/local/lib',])
        	env.AppendUnique(FRAMEWORKS='qwt')      

        self.settings['RPATH'] = [qwt_libdir]
        self.settings['CPPPATH'] = [os.path.join(qwt_dir, 'include')]
        plugindir='$QWTDIR/designer/plugins/designer'
        self.settings['QT_UICIMPLFLAGS'] = ['-L', plugindir]
        self.settings['QT_UICDECLFLAGS'] = ['-L', plugindir]


    def apply_settings(self, env):

        try:
            env['QWTDIR'] = self.settings['QWTDIR']
        except KeyError:
            return

        if not env.has_key('QWT_DOXREF'):
            env['QWT_DOXREF'] = self.settings['QWT_DOXREF']
        env.AppendDoxref(env['QWT_DOXREF'])

        if (self.settings['QWTDIR'] == USE_PKG_CONFIG):
            # Don't try here to make things unique in CFLAGS; just do an append
            env.ParseConfig('pkg-config --cflags Qwt', unique = False)
            env.ParseConfig('pkg-config --libs Qwt', unique = False)
            return

        if env['PLATFORM'] != 'darwin':
	        env.Append(LIBS=self.settings['LIBS'])
	        if not self.building:
	            env.AppendUnique(LIBPATH=self.settings['LIBPATH'])

        env.AppendUnique(RPATH=self.settings['RPATH'])
        env.Append(CPPPATH=self.settings['CPPPATH'])
        env.Append(QT_UICIMPLFLAGS=self.settings['QT_UICIMPLFLAGS'])
        env.Append(QT_UICDECLFLAGS=self.settings['QT_UICDECLFLAGS'])

def enable_qwt(env):
    # This configure test for qwt must be delayed, and not done
    # by the generate() function when this qwt tool is loaded.
    # This is because the qt4 build environment is not fully setup
    # when qt4 tool is loaded via its generate() function. The
    # user must call env.EnableQt4Modules(['QtCore',...]) after the
    # qt4 tool is loaded to setup the Qt build environment.
    # Then call env.EnableQwt(), and this Configure check has
    # a chance of succeeding.
    conf = Configure(env,clean=False,help=False)
    hasQwt = conf.CheckCXXHeader('qwt.h')
    conf.Finish()
    return hasQwt

qwt_package = QwtPackage()

def find_qwtdir(env):
    qwtdir = None
    #
    # See if pkg-config knows about Qwt on this system
    #
    try:
        pkgConfigKnowsQwt = (os.system('pkg-config --exists Qwt') == 0)
    except:
        pkgConfigKnowsQwt = 0
    # 
    # Try to find the Qwt installation location, trying in order:
    #    o command line QWTDIR option (or otherwise set in the environment)
    #    o OS environment QWTDIR
    #    o installation defined via pkg-config (this is the preferred method)
    #    o lastly see if lib_/libqwt.so exists under OPT_PREFIX
    #
    if (env.has_key('QWTDIR')):
        qwtdir = env['QWTDIR']
    elif (os.environ.has_key('QWTDIR')):
        qwtdir = os.environ['QWTDIR']
    elif pkgConfigKnowsQwt:
        qwtdir = USE_PKG_CONFIG
    elif (env.has_key('OPT_PREFIX') and 
          os.path.exists(os.path.join(env['OPT_PREFIX'], lib_, 'libqwt.so'))):
        qwtdir = env['OPT_PREFIX']
    print("qwtdir set to '%s'" % (qwtdir))
    return qwtdir


def generate(env):
    global _options
    if not _options:
        _options = env.GlobalVariables()
        _options.AddVariables(PathVariable('QWTDIR', 'Qwt installation root.', None))
    _options.Update(env)

    #
    # One-time stuff if this tool hasn't been loaded yet
    #
    if (not env.has_key(myKey)):
        #
        # We should also require Qt here, but which version?
        #
        #env.Require(['qt', 'doxygen'])
	env.Require(['doxygen'])
        
    qwt_package.require(env)
    env[myKey] = True


def exists(env):
    return True

