
import os
import SCons
from SCons.Options import PathOption
import eol_scons.chdir
from eol_scons.package import Package
import string

options = None
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

class QwtPackage(Package):

    def __init__(self):
        headers = [os.path.join("include",f) for f in qwt_headers]
        libs = ["$QWTDIR/lib/libqwt.so"]
        Package.__init__(self, "QWT", ["qwt.pro"]+headers,
                         qwt_actions, libs,
                         default_package_file = "qwt-4.2.0.zip")

    def checkBuild(self, env):
        if env['PLATFORM'] == 'win32':
            return
        qwt_dir = env['QWTDIR']
        libqwt = os.path.join(qwt_dir, 'lib', 'libqwt.so')
        if not os.access(libqwt, os.R_OK):
            # Not installed in the given QWTDIR, so try internal path
            qwt_dir = self.getPackagePath(env)
            env['QWTDIR'] = qwt_dir
        Package.checkBuild(self, env)


    def require(self, env):

        # The actual QWTDIR value to use depends upon whether qwt is being
        # built internally or not.  Check here to see if the QWTDIR option
        # points to an existing library, and if not then resort to the
        # package build location.

        env.Tool('download')
        env.Tool('unpack')
        Package.checkBuild(self, env)
        qwt_dir = env['QWTDIR']
        qwt_libdir = os.path.join(qwt_dir, 'lib')
        libqwt = os.path.join(qwt_libdir, 'libqwt.so')
        #
        # Unless we're building, only generate stuff for -I<>, -R<>,
        # and -L<> options here.  We let someone else handle the
        # -l<> options later.
        #
        if self.building:
            env.Append(LIBS=[env.File(libqwt)])
        else:
            env.AppendUnique(LIBPATH= [qwt_libdir, ])
        env.AppendUnique(RPATH=[qwt_libdir])

        env.Append(CPPPATH= [os.path.join(qwt_dir, 'include'),])
        plugindir='$QWTDIR/designer/plugins/designer'
        env.Append(QT_UICIMPLFLAGS=['-L',plugindir])
        env.Append(QT_UICDECLFLAGS=['-L',plugindir])
        env.Append(DEPLOY_SHARED_LIBS='qwt')
        qwt_docdir = os.path.join(qwt_dir, 'doc', 'html')
        if not env.has_key('QWT_DOXREF'):
            env['QWT_DOXREF'] = 'qwt:' + qwt_docdir
        env.AppendDoxref(env['QWT_DOXREF'])

qwt_package = QwtPackage()

def generate(env):
    global options
    if not options:
        options = env.GlobalOptions()
        options.AddOptions(PathOption('QWTDIR', 'Qwt installation root.', None))

    options.Update(env)
    #
    # See if pkg-config knows about Qwt on this system
    #
    try:
        pkgConfigKnowsQwt = (os.system('pkg-config --exists Qwt') == 0)
    except:
        pkgConfigKnowsQwt = 0

    #
    # One-time stuff if this tool hasn't been loaded yet
    #
    if (not env.has_key(myKey)):
        #
        # We should also require Qt here, but which version?
        #
        #env.Require(['qt', 'doxygen'])
	env.Require(['doxygen'])
        
        # 
        # Try to find the Qwt installation location, trying in order:
        #    o command line QWTDIR option
        #    o OS environment QWTDIR
        #    o installation defined via pkg-config (this is the preferred method)
        # At the end of checking, either env['QWTDIR'] will contain the path
        # to the top of the installation, or it will be set to USE_PKG_CONFIG, 
        # or we will raise an exception.
        #
        if (env.has_key('QWTDIR')):
            pass
        elif (os.environ.has_key('QWTDIR')):
            env['QWTDIR'] = os.environ['QWTDIR']
        elif pkgConfigKnowsQwt:
            env['QWTDIR'] = USE_PKG_CONFIG
        else:
            raise SCons.Errors.StopError, "Qwt not found"
        
        #
        # First-time-only stuff here: -I<>, -D<>, and -L<> options
        # The -l<> stuff we do later every time this tool is loaded
        #   
        if (env['QWTDIR'] is USE_PKG_CONFIG):
            env.ParseConfig('pkg-config --cflags Qwt')
        else:
            qwt_package.require(env)
            
        env[myKey] = True
    #
    # Add -lqwt each time this tool is requested
    #
    if (env['QWTDIR'] is USE_PKG_CONFIG):
        env.ParseConfig('pkg-config --libs Qwt')
    else:
        env.Append(LIBS = ['qwt'])        

def exists(env):
    return True

