import os,os.path
import SCons
from SCons.Options.EnumOption import EnumOption
from SCons.Builder import Builder
import string

from chdir import ChdirActions
import eol_scons

_options = eol_scons.Pkg_Options()
_options.AddOptions(
    EnumOption('packagebuilds',
               'Control automatic package building.',
               'disable',
               allowed_values=('disable', 'enable', 'force')))

DEBUG = 0

class Package:
    """
    Base class for packages which abstracts the operations and services
    provided by a package, such as its _REQUIRE function and the ability to
    build and install a package automatically from an archive.
    """

    # The archive targets are relative to the top directory of the archive,
    # so an archive which contains an INSTALL file just passes "INSTALL"
    # as a target file.
    #
    # Install targets are absolute, but they can contain environment
    # variables.  The targets are expanded with env.subst() in the default
    # emitter method.  If the install_targets are not passed in the
    # constructor, then the getInstallTargets() method must be overridden.
    #
    def __init__(self, name,
                 archive_targets,
                 build_actions,
                 install_targets,
                 default_package_file = None):
        self.name = name
        self.building = 0
        self.checked = 0
        self.debug = DEBUG
        if type(archive_targets) is not type([]):
            archive_targets = [ archive_targets ]
        self.archive_targets = archive_targets
        self.build_actions = build_actions
        self.install_targets = install_targets
        self.default_package_file = default_package_file
        self.build_targets = None

    def getArchiveTargets(self):
        return self.archive_targets

    def getInstallTargets(self):
        return self.install_targets

    def getPackageFile(self, env):
        key = "%s_PACKAGE_FILE" % (self.name)
        if env.has_key(key):
            return env[key]
        return self.default_package_file

    def getPackageName(self, env):
        return env.getPackageName(self.getPackageFile(env))

    def getPackagePath(self, env):
        dir = env.Dir(os.path.join ("#", self.getPackageName(env)))
        return dir.get_abspath()

    def unpackPackage(self, env):
        env.Tool('download')
        env.Tool('unpack')
        pkgfile = self.getPackageFile(env)
        pkgname = self.getPackageName(env)
        # Prepend the archive directory to all of the targets and
        # expand them in case they contain construction variables.
        contents = [ env.subst(os.path.join("#",pkgname,path))
                     for path in self.getArchiveTargets() ]
        if self.debug:
            print pkgdir, pkgfile, pkgname
            print contents

        localfile = env.Download(pkgfile)
        targets = env.Unpack(contents, localfile)
        return targets

    def setupBuild(self, env):
        print "Setting up to build %s package..." % (self.name)
        global _options
        _options.Update(env)
        self.building = 1
        builder = self.generate(env)
        pkgsource = self.unpackPackage(env)
        if self.debug:
            print "Created rules to unpack %s" % (str(pkgsource[0]))
        self.build_targets = builder(source = pkgsource, env = env)
        return self.build_targets

    def checkBuild(self, env):
        """
        Add settings to the environment required to build against this
        package, including possibly adding the targets to build the package
        itself.
        """
        global _options
        _options.Update(env)
        # If not checked yet, see if all of the install targets already
        # exist or not.
        if self.checked:
            return self.build_targets
        self.checked = 1
        if env['packagebuilds'] == 'disable':
            if self.debug:
                print "packagebuilds disabled, %s is not being checked." % \
                      self.name
            return self.build_targets
        complete = 1
        # Turn on the 'building' flag, since even if the targets are found
        # and don't need to actually be built, we want to build against
        # those built package targets rather than the external
        # alternatives.
        self.building = 1
        for path in self.getInstallTargets():
            spath = env.subst(path)
            if not os.access(spath, os.R_OK):
                print "%s: %s is missing." % (self.name, spath)
                complete = 0
                break
        if not complete or env['packagebuilds'] == 'force':
            if complete:
                print "%s is installed, but building anyway." % self.name
            self.setupBuild(env)
        return self.build_targets

    def emitter(self, target, source, env):
        "Expand the target paths."
        targets = [ env.subst(path) for path in self.getInstallTargets() ]
        return targets, source

    def getBuilderName(self, env):
        return "Build%s" % (self.name)

    def generate(self, env):
        "Create Builder for building this package from its extracted archive."
        actions = ChdirActions(env, self.build_actions, "$SOURCE.dir")
        builder = Builder (action = actions, emitter = self.emitter)
        env['BUILDERS'][self.getBuilderName(env)] = builder
        if self.debug:
            print "%s created." % self.getBuilderName(env)
        return builder

