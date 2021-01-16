
import os
import sys
import re

_options = None

# Maybe this should be split into two tools: one for setting an OPT_PREFIX
# for finding dependencies and one for setting up the INSTALL_PREFIX and
# all of the install methods.  The INSTALL_PREFIX can default to OPT_PREFIX
# when it exists.

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


def AppendCppLastPath(env, incdir):
    # We want the opt path to be last, since it is a fallback for any
    # headers not found in the source tree or in other specific
    # directories.  Do that by duplicating _CPPINCFLAGS except for a
    # different variable, CPPLASTPATH.  _CPPINCFLAGS is actually a
    # complicated function call which expands CPPPATH into the compiler
    # flags.  This tries to be portable and simple by using duplicating the
    # same construct but for a different path variable, CPPLASTPATH.
    if 'CPPLASTPATH' not in env:
        cppincflags = env['_CPPINCFLAGS']
        lastincflags = re.sub(r"\bCPPPATH\b", 'CPPLASTPATH', cppincflags)
        env['_CPPINCFLAGS'] = cppincflags + ' ' + lastincflags
        env['CPPLASTPATH'] = []
    env.AppendUnique(CPPLASTPATH=[incdir])


def AppendLibLastPath(env, libdir):
    # Same as AppendCppLastPath except for LIBPATH.
    if 'LIBLASTPATH' not in env:
        libdirflags = env['_LIBDIRFLAGS']
        lastlibflags = re.sub(r"\bLIBPATH\b", 'LIBLASTPATH', libdirflags)
        env['_LIBDIRFLAGS'] = libdirflags + ' ' + lastlibflags
        env['LIBLASTPATH'] = []
    env.AppendUnique(LIBLASTPATH=[libdir])


def OptPrefixSetup(env):
    # If OPT_PREFIX does not exist in this environment, or if it is
    # explicitly set to empty, or if it was left as $DEFAULT_OPT_PREFIX but
    # DEFAULT_OPT_PREFIX has not been set, then that disables all
    # OPT_PREFIX settings.  Therefore if the intention is to set a value
    # for DEFAULT_OPT_PREFIX which always takes effect, it must be set
    # before this tool is applied.
    opt_prefix = env.subst(env.get('OPT_PREFIX', ''))
    if not opt_prefix:
        return env
    # Use the expanded variables to check for path existence.
    opt_lib=os.path.join(opt_prefix, "lib")
    opt_inc=os.path.join(opt_prefix, "include")
    opt_bin=os.path.join(opt_prefix, "bin")
    if os.path.exists(opt_bin):
        # Prepend opt bin path so that -config tools like log4cpp-config
        # will be found first and used.
        env.PrependENVPath('PATH', opt_bin)
    if os.path.exists(opt_lib):
        env.AppendUnique(RPATH=[opt_lib])
        AppendLibLastPath(env, opt_lib)
    if os.path.exists(opt_inc):
        AppendCppLastPath(env, opt_inc)
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

def InstallPrefixSetup(env):
    # Rather than depend upon OPT_PREFIX to be set, supply our own default
    # if no other default has been set.  Unlike OPT_PREFIX, the install
    # methods all depend upon some reasonable install path.  The default
    # install prefix has no affect unless INSTALL_PREFIX has not been
    # changed.
    if not env.subst(env.get('DEFAULT_INSTALL_PREFIX','')):
        if sys.platform == 'darwin':
            env['DEFAULT_INSTALL_PREFIX'] = '/usr/local'
        else:
            env['DEFAULT_INSTALL_PREFIX'] = '/opt/local'

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
    InstallPrefixSetup(env)

def exists(env):
    return True
