
import os
import eol_scons
import SCons
import new

_options = None


def SetupVariables(env):
    global _options
    _options = env.GlobalVariables()
    default_opt = '$DEFAULT_OPT_PREFIX'
    default_install = '$DEFAULT_INSTALL_PREFIX'
    _options.Add ('OPT_PREFIX',
                  "The common prefix for external tools and libraries.",
                  default_opt)
    _options.Add ('INSTALL_PREFIX',
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


# An 'install' alias is provided to allow the user to invoke "scons -u
# install".  It works by adding targets to the 'install' alias when defined
# through one of the Install methods below, *including* the standard
# Install() and InstallAs() methods.  Several other methods have been tried
# which did not involve overriding the standard install methods.  At one
# point, 'install' was an alias for the root INSTALL_PREFIX path, causing
# everything destined for that tree to be installed.  That works to a
# point, except it would be better to add the individual install
# subdirectories, since sometimes the INSTALL_PREFIX points to the top of
# the source tree, in which case 'install' would become an alias to build
# everything, even those targets not needed for an install.  However, if
# any of the install paths do not exist or are not needed, then this scheme
# breaks down, because scons wants the alias dependencies (the install
# paths) to exist.  Then SCons reports an error like this:
#
#  scons: *** Source `conf' not found, needed by target `install'.  Stop.
#
# Using Ignore() does not seem to work either, because it ignores
# dependencies of a target, but in this case we need to ignore the
# particular source (the install directory) if there will be no installs to
# it.
#
# Recent versions of scons have a FindInstalledFiles() method, and that
# returns exactly the list of files for which we would like to add an
# alias.  However, using that would require a hook to add the alias after
# all the targets have been specified, ie, after all the SConscript files
# have been read, and I cannot find any such hook in SCons yet.
#
# So we end up with the current scheme of 'extending' the standard Install
# and InstallAs methods to add the 'install' alias automatically.  This
# could break some existing eol_scons setups, but it should work more as
# expected for those setups that count on a 'default' install alias to
# install everything under INSTALL_PREFIX.

def Install (self, *args, **kw):
    """Add 'install' alias to targets created with standard Install() method."""
    inst = self._prefixoptions_StandardInstall(*args, **kw)
    self.Alias('install', inst)
    return inst

def InstallAs (self, *args, **kw):
    """Add 'install' alias to targets created with standard Install() method."""
    inst = self._prefixoptions_StandardInstallAs (*args, **kw)
    self.Alias('install', inst)
    return inst

def InstallLibrary (self, source):
    """Convenience method to install a library into INSTALL_LIBDIR."""
    return self.Install (self['INSTALL_LIBDIR'], source)

def InstallPythonLibrary (self, source):
    """
    Convenience method to install a python library into INSTALL_PYTHON_LIBDIR.
    """
    return self.Install (self['INSTALL_PYTHON_LIBDIR'], source)

def InstallProgram (self, source):
    return self.Install (self['INSTALL_BINDIR'], source)

def InstallConfig (self, source):
    return self.Install (self['INSTALL_CONFIGDIR'], source)

def InstallEtc (self, source):
    return self.Install (self['INSTALL_ETCDIR'], source)

def InstallShare (self, subdir, source):
    """
    Install <source> at INSTALL_DIR/share/<subdir>/<source>
    """
    dir = os.path.join(self['INSTALL_SHAREDIR'], subdir)
    return self.Install (dir, source)

def InstallHeaders (self, subdir, source):
    incdir = os.path.join(self['INSTALL_INCDIR'],subdir)
    return self.Install (incdir, source)


def generate(env):
    """
    Use the given paths as defaults for the opt and install prefix
    directories, else base the default on the OS release.
    """
    global _options
    if not _options:
        SetupVariables(env)
    # Generate installation paths according to options and defaults
    _options.Update(env)
    OptPrefixSetup(env)
    env['INSTALL_LIBDIR'] = "$INSTALL_PREFIX/lib"
    env['INSTALL_BINDIR'] = "$INSTALL_PREFIX/bin"
    env['INSTALL_INCDIR'] = "$INSTALL_PREFIX/include"
    env['INSTALL_CONFIGDIR'] = "$INSTALL_PREFIX/conf"
    env['INSTALL_ETCDIR'] = "$INSTALL_PREFIX/etc"
    env['INSTALL_PYTHON_LIBDIR'] = "$INSTALL_PREFIX/lib/python"
    env['INSTALL_SHAREDIR'] = "$INSTALL_PREFIX/share"
    # Here we install the install convenience methods, since they do not
    # work unless the install prefix variables have been set.  These
    # must be set only once, else infinite recursion ensues.
    try:
        method = getattr(env, '_prefixoptions_StandardInstall')
        return
    except AttributeError:
        pass
    env._prefixoptions_StandardInstall = env.Install
    env._prefixoptions_StandardInstallAs = env.InstallAs
    env.AddMethod(Install)
    env.AddMethod(InstallAs)
    env.AddMethod(InstallEtc)
    env.AddMethod(InstallConfig)
    env.AddMethod(InstallLibrary)
    env.AddMethod(InstallProgram)
    env.AddMethod(InstallHeaders)
    env.AddMethod(InstallPythonLibrary)
    env.AddMethod(InstallShare)

def exists(env):
    return True
