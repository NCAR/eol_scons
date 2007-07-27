
import os
import eol_scons.chdir
from eol_scons.package import Package
import string

options = None

# The header files are unpacked directly into the QWT_DIR/include
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
        libs = ["$QWT_DIR/lib/libqwt.so"]
        Package.__init__(self, "QWT", ["qwt.pro"]+headers,
                         qwt_actions, libs,
                         default_package_file = "qwt-4.2.0.zip")

    def setupBuild(self, env):
        # Make sure QWT_DIR is overridden with the build location
        # before the install targets get expanded by the builder.
        qwt_dir = env['QWT_DIR']
        env['QWT_DIR'] = qwt_dir
        installs = Package.setupBuild(self, env)
        env.AddGlobalTarget('libqwt', installs[0])

    def require(self, env):

        # The actual QWT_DIR value to use depends upon whether qwt is being
        # built internally or not.  Check here to see if the QWT_DIR option
        # points to an existing library, and if not then resort to the
        # package build location.

        env.Tool('download')
        env.Tool('unpack')
        qwt_dir = env['QWT_DIR']
        library = os.path.join(qwt_dir, 'lib', 'libqwt.so')
        if not os.access(library, os.R_OK):
            # Not installed in the given QWT_DIR, so try internal path
            qwt_dir = self.getPackagePath(env)
            env['QWT_DIR'] = qwt_dir
        Package.checkBuild(self, env)
        if self.building:
            libqwt = env.GetGlobalTarget('libqwt')
            env.Append(LIBS=[libqwt])
        else:
            qwt_libdir = os.path.join(qwt_dir, 'lib')
            env.Append(LIBPATH= [qwt_libdir, ])
            env.Append(LIBS=['qwt',])
            env.AppendUnique(RPATH=[qwt_libdir])

        env.Append(CPPPATH= [os.path.join(qwt_dir, 'include'),])
        plugindir='$QWT_DIR/designer/plugins/designer'
        env.Append(QT_UICIMPLFLAGS=['-L',plugindir])
        env.Append(QT_UICDECLFLAGS=['-L',plugindir])
        env.Append(DEPLOY_SHARED_LIBS='qwt')
        env.Require(['PKG_QT'])
        qwt_docdir = os.path.join(qwt_dir, 'doc', 'html')
        if not env.has_key('QWT_DOXREF'):
            env['QWT_DOXREF'] = 'qwt:' + qwt_docdir
        env.AppendDoxref(env['QWT_DOXREF'])

qwt_package = QwtPackage()

def generate(env):
    global options
    if not options:
        options = env.GlobalOptions()
        options.Add('QWT_DIR', 'Set the Qwt directory.', 
                    env.FindPackagePath('QWT_DIR', '$OPT_PREFIX/qwt*',
                                        '/opt/qwt'))
    options.Update(env)
    qwt_package.require(env)

def exists(env):
    return True

