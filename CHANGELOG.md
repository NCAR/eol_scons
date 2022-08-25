# Changelog

Changelog for eol_scons.

## [Unreleased]

- eol_scons should now be installed as a subdirectory of site_scons.  Prior to
  this, the eol_scons repository was typically cloned into `~/.scons` and
  named `site_scons`, or else it was added to a project as a git submodule
  named `site_scons`.  This practice interferes with adding other SCons
  extensions under the `site_scons` directory, and it is confusing that the
  repository is cloned with a different name.  Now the `site_scons` directory
  must be created first, either as part of the project or in `~/.scons`, then
  the eol_scons repository can be cloned into that directory with the name
  `eol_scons`.  The new `__init__.py` file in the top directory takes care of
  adding the `eol_scons/eol_scons` directory to the path of the `eol_scons`
  package.  Importing `eol_scons` using the old scheme prints a deprecation
  message.
- eol_scons now requires Python 3.6.  SCons 4.0 requires Python 3.5, SCons
  4.4 requires Python 3.6, so eol_scons is following suit.  The biggest
  known issue with this is that on RHEL7 the default python and scons is
  still python 2.7.  There is a scons package based on python3,
  python36-scons, but it must be invoked as `scons-3`.  The RPM spec has
  been updated to force byte compiling with python3 with an install
  dependency on `scons-python3`.
- Add `gitinfo` variable.  When set to `off`, the `gitinfo` tool will try
  to load repo version info from a generated header instead of running
  `git` tools.  This allows builds in source archives to use the repo
  version info, like for RPM packages.
- Add `gitdump` target.  For each directory where the `gitinfo` tool collects
  repo info, there is a target which prints the repo info.  The target must be
  named on the command-line, like `scons ./gitdump`.
- The eol_scons override of the `Install()` method can be disabled by
  calling `eol_scons.EnableInstallAlias(False)`.  It still defaults to
  enabled, but someday could be deprecated.  This allows projects to choose
  different install aliases, like _install_ and _install.root_ and
  _install.doc_.  There was also a change to allow the `Install()` override
  to work with the standard SCons option `--install-sandbox`.
- Consolidate the `buildmode` settings into the single tool rather than
  providing separate tools for `warnings`, `debug`, and so on.  This fixes a
  problem with SCons 4.4 where a python built-in module actually tries to
  import `warnings`.
- Remove runtime ld path (-R link option) in many places, partly to facilitate
  MacOS builds.
- Print all targets in `FindInstalledFiles()` with `-h --list-installs`.
- Some messages printed by eol_scons, especially the initial boilerplate about
  loading configs, can now be suppressed with the SCons `-Q` (*no_progress*)
  option.  SConscript files and tools can use the `PrintProgress()` method to
  print messages which should be suppressed by `-Q`.

## [4.1] - 2021-01-25

- Refactor for Qt5 modules, providing tools named after the module which apply
  that module for the project Qt version.
- In prefixoptions tool, make sure optional extra search paths are always
  added last to `CPPPATH` and `LIBPATH`.
- Port to SCons 4.1, removing use of `SCons.Warnings.Warning`.
- Add `jsoncpp` tool.

## [3.0] - 2017-12-21

- Port to SCons 3.0 and python 3.

## [2.9] - 2017-12-18

- last tagged release before scons 3.0 port

## [2.0] - 2015-10-05

- first tagged release

<!-- Versions -->
[unreleased]: https://github.com/NCAR/eol_scons/compare/v4.1...HEAD
[4.1]: https://github.com/NCAR/eol_scons/compare/v3.0...v4.1
[3.0]: https://github.com/NCAR/eol_scons/compare/v2.9...v3.0
[2.9]: https://github.com/NCAR/eol_scons/compare/v2.0...v2.9
[2.0]: https://github.com/NCAR/eol_scons/releases/tag/v2.0
