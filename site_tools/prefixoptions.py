
import os
import eol_scons
import SCons
import new

options = None


def SetupOptions(env):
    global options
    options = env.GlobalOptions()
    default_opt = '$DEFAULT_OPT_PREFIX'
    default_install = '$DEFAULT_INSTALL_PREFIX'
    options.Add ('OPT_PREFIX',
                 "The common prefix for external tools and libraries.",
                 default_opt)
    options.Add ('INSTALL_PREFIX',
                 "The root installation directory for bin, lib, and include.",
                 default_install)


def OptPrefixSetup(env):
    if not env.has_key('OPT_PREFIX') or len(env['OPT_PREFIX']) == 0:
        return env
    if not env.has_key('DEFAULT_OPT_PREFIX'):
        env['DEFAULT_OPT_PREFIX'] = '/opt/local'
    if not env.has_key('DEFAULT_INSTALL_PREFIX'):
        env['DEFAULT_INSTALL_PREFIX'] = '$OPT_PREFIX'
    opt_lib=os.path.join(env['OPT_PREFIX'], "lib")
    opt_inc=os.path.join(env['OPT_PREFIX'], "include")
    opt_bin=os.path.join(env['OPT_PREFIX'], "bin")
    if os.path.exists(opt_bin):
        # Prepend opt bin path so that -config tools like log4cpp-config
        # will be found first and used.
        env.PrependENVPath('PATH', opt_bin)
    if os.path.exists(opt_lib):
        env.AppendUnique(RPATH=opt_lib)
        env.AppendUnique(LIBPATH=[opt_lib] )
    if os.path.exists(opt_inc):
        env.AppendUnique(CPPPATH=[opt_inc] )
    return env


def _InstallLibrary (self, source):
    """Convenience method to install a library into INSTALL_LIBDIR."""
    return self.Install (self['INSTALL_LIBDIR'], source)


def _InstallProgram (self, source):
    return self.Install (self['INSTALL_BINDIR'], source)


def _InstallHeaders (self, subdir, source):
    incdir = os.path.join(self['INSTALL_INCDIR'],subdir)
    return self.Install (incdir, source)


def generate(env):
    """
    Use the given paths as defaults for the opt and install prefix
    directories, else base the default on the OS release.
    """
    global options
    if not options:
        SetupOptions(env)
    # Generate installation paths according to options and defaults
    options.Update(env)
    OptPrefixSetup(env)
    env['INSTALL_LIBDIR'] = "$INSTALL_PREFIX/lib"
    env['INSTALL_BINDIR'] = "$INSTALL_PREFIX/bin"
    env['INSTALL_INCDIR'] = "$INSTALL_INCDIR/include"
    # Here we install the install convenience methods, since they do not
    # work unless the install prefix variables have been set.
    env.InstallLibrary = new.instancemethod(_InstallLibrary, env, env.__class__)
    env.InstallProgram = new.instancemethod(_InstallProgram, env, env.__class__)
    env.InstallHeaders = new.instancemethod(_InstallHeaders, env, env.__class__)


def exists(env):
    return True
